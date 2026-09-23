#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch the BT Audio renderer for the fixed V5.2 layout.

This is the third step of the GitHub patch-kit:
  1. apply_patch_v3.py   - receive Bluetooth metadata from CAN 0x4B1
  2. apply_render.py      - keep the title buffer safe for long metadata
  3. apply_layout_v5_2.py - draw artist/title/album at fixed centred rows

Input and output are raw 0x5000-based code-partition payloads, not VBF files.
The script deliberately refuses an unexpected hook, a missing renderer patch,
or a non-empty code cave.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path


BASE = 0x5000
CAVE = 0x83380
HOOK = 0x1CF40
HOOK_OLD = bytes.fromhex("2078f023fd7e")
RENDER_SITES = (0x1CEDC, 0x1CEFE, 0x1CF1A, 0x1CF32, 0x1CF4A)
RENDER_WORD = 0xA810  # add r0,sp,#0x40, written by apply_render.py


def hw(value: int) -> bytes:
    return struct.pack(">H", value & 0xFFFF)


def ebl(src: int, dst: int) -> bytes:
    """Encode a big-endian Thumb BL used by the MAC7116 firmware."""
    offset = (dst - (src + 4)) & 0x1FFFFFF
    sign = (offset >> 24) & 1
    i1 = (offset >> 23) & 1
    i2 = (offset >> 22) & 1
    imm10 = (offset >> 12) & 0x3FF
    imm11 = (offset >> 1) & 0x7FF
    j1 = (~(i1 ^ sign)) & 1
    j2 = (~(i2 ^ sign)) & 1
    return struct.pack(">HH",
                       0xF000 | (sign << 10) | imm10,
                       0xD000 | (j1 << 13) | (j2 << 11) | imm11)


def build_cave() -> bytes:
    """Build the fixed-row renderer cave with resolved local branches."""
    code = bytearray()
    labels: dict[str, int] = {}
    branches: list[tuple[int, int, str, int | None]] = []
    literals: list[tuple[int, int, int, str]] = []
    local_bls: list[tuple[int, int, str]] = []

    def emit16(value: int) -> None:
        code.extend(hw(value))

    def label(name: str) -> None:
        labels[name] = CAVE + len(code)

    def bl(target: int | str) -> None:
        address = CAVE + len(code)
        if isinstance(target, str):
            local_bls.append((len(code), address, target))
            code.extend(b"\x00\x00\x00\x00")
        else:
            code.extend(ebl(address, target))

    def branch(name: str, condition: int | None = None) -> None:
        address = CAVE + len(code)
        branches.append((len(code), address, name, condition))
        emit16(0)

    def ldr_literal(reg: int, name: str) -> None:
        address = CAVE + len(code)
        literals.append((len(code), address, reg, name))
        emit16(0)

    # Save the caller and run the stock width limiter on the album buffer.
    emit16(0xB510)             # push {r4,lr}
    emit16(0x1C29)             # mov r1,r5 (active layout)
    emit16(0xA808)             # add r0,sp,#0x20 (caller's sp+0x18 album)
    bl(0x1CCEA)                # stock media string width limiter
    emit16(0xAB08)             # add r3,sp,#0x20
    emit16(0x781C)             # ldrb r4,[r3,#0]
    emit16(0x2C00)             # cmp r4,#0
    branch("no_album", 0)      # beq

    # The stock getter can fall back from an empty artist to the album.
    # Check the original artist buffer so the album is not drawn twice.
    emit16(0xAB0D)             # add r3,sp,#0x34 (caller's sp+0x2c artist)
    emit16(0x781C)             # ldrb r4,[r3,#0]
    emit16(0x2C00)             # cmp r4,#0
    branch("gray_three_line", 0)
    emit16(0x2078)             # white style id 120
    bl(0x40A42)
    emit16(0x2278)             # Y=120
    emit16(0xA817)             # processed artist at caller's sp+0x54
    bl("axis")

    label("gray_three_line")
    emit16(0x2079)             # gray style id 121
    bl(0x40A42)
    emit16(0x228F)             # Y=143
    emit16(0xA812)             # processed title at caller's sp+0x40
    bl("axis")
    emit16(0x22A6)             # Y=166
    emit16(0xA808)             # album at caller's sp+0x18
    bl("axis")
    emit16(0xBD10)             # pop {r4,pc}

    label("no_album")
    emit16(0x2078)             # white artist
    bl(0x40A42)
    emit16(0x2278)             # Y=120
    emit16(0xA817)             # processed artist
    bl("axis")
    emit16(0x2079)             # gray title
    bl(0x40A42)
    emit16(0x228F)             # Y=143
    emit16(0xA812)             # processed title
    bl("axis")
    emit16(0xBD10)             # pop {r4,pc}

    # Use optical X=297 on the photographed/observed layout. Keep the stock
    # X=216 path for the alternate layout that was not observed physically.
    label("axis")
    emit16(0x2D00)             # cmp r5,#0
    branch("axis_original", 1)
    emit16(0x21FF)             # mov r1,#255
    emit16(0x312A)             # add r1,#42 => 297
    ldr_literal(3, "center_ptr")
    emit16(0x4718)             # bx r3
    label("axis_original")
    emit16(0x21D8)             # mov r1,#216
    ldr_literal(3, "original_ptr")
    emit16(0x4718)             # bx r3

    while (CAVE + len(code)) & 3:
        emit16(0x46C0)         # nop / align literals
    label("center_ptr")
    code.extend(struct.pack(">I", 0x409F3))
    label("original_ptr")
    code.extend(struct.pack(">I", 0x409EB))

    for offset, address, name, condition in branches:
        target = labels[name]
        delta = target - (address + 4)
        assert delta % 2 == 0
        half = delta // 2
        if condition is None:
            assert -1024 <= half <= 1023
            instruction = 0xE000 | (half & 0x7FF)
        else:
            assert -128 <= half <= 127
            instruction = 0xD000 | (condition << 8) | (half & 0xFF)
        code[offset:offset + 2] = hw(instruction)

    for offset, address, name in local_bls:
        code[offset:offset + 4] = ebl(address, labels[name])

    for offset, address, reg, name in literals:
        target = labels[name]
        base = (address + 4) & ~3
        delta = target - base
        assert delta >= 0 and delta % 4 == 0 and delta // 4 <= 255
        code[offset:offset + 2] = hw(0x4800 | (reg << 8) | (delta // 4))

    return bytes(code)


def patch_payload(payload: bytes) -> tuple[bytes, int]:
    if len(payload) < 0x83500 - BASE:
        raise ValueError("payload is too short for the 1412-FL renderer patch")

    raw = bytearray(payload)
    hook_offset = HOOK - BASE
    cave_offset = CAVE - BASE
    if bytes(raw[hook_offset:hook_offset + len(HOOK_OLD)]) != HOOK_OLD:
        got = raw[hook_offset:hook_offset + 6].hex()
        raise ValueError(f"renderer hook mismatch at 0x{HOOK:x}: got {got}")

    for address in RENDER_SITES:
        offset = address - BASE
        got = struct.unpack(">H", raw[offset:offset + 2])[0]
        if got != RENDER_WORD:
            raise ValueError(
                f"apply_render.py was not applied at 0x{address:x}: "
                f"got 0x{got:04x}, expected 0x{RENDER_WORD:04x}"
            )

    cave = build_cave()
    if CAVE + len(cave) > 0x83500:
        raise AssertionError("renderer cave exceeds the reserved free area")
    if any(raw[cave_offset:cave_offset + len(cave)]):
        raise ValueError("renderer code cave is not empty; refusing to overwrite it")

    raw[hook_offset:hook_offset + 6] = ebl(HOOK, CAVE) + bytes.fromhex("e01b")
    raw[cave_offset:cave_offset + len(cave)] = cave
    return bytes(raw), len(cave) + 6


def self_test() -> None:
    payload = bytearray(0xFB000)
    payload[HOOK - BASE:HOOK - BASE + 6] = HOOK_OLD
    for address in RENDER_SITES:
        payload[address - BASE:address - BASE + 2] = hw(RENDER_WORD)
    patched, changed = patch_payload(bytes(payload))
    assert changed == 126
    assert patched != payload
    try:
        patch_payload(patched)
    except ValueError:
        pass
    else:
        raise AssertionError("second patch unexpectedly succeeded")
    print("PASS: V5.2 renderer patch self-test; changed bytes:", changed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="raw 0x5000-based code payload")
    parser.add_argument("output", nargs="?", help="patched raw payload")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.input or not args.output:
        parser.error("input and output are required unless --self-test is used")

    source = Path(args.input)
    destination = Path(args.output)
    patched, changed = patch_payload(source.read_bytes())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(patched)
    print(f"Saved {destination} ({len(patched)} B); changed bytes: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
