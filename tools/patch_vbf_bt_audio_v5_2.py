#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-command patcher for a user's own Convers+ VBF.

Pipeline:
  1. verify the input VBF;
  2. unpack its 0x5000 code payload;
  3. add Bluetooth CAN metadata reception (GitHub upstream patch v3);
  4. apply the safe title-buffer relocation;
  5. apply the V5.2 fixed centred layout;
  6. repack the result as a new VBF with recalculated CRCs.

No Ford firmware, VIN or EEPROM is included or uploaded by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


BASE = 0x5000
PART_NUMBER = "CS7T-14C026-CD"
DEFAULT_CAN_ID = 0x4B1
# SHA-256 of the known clean 0x5000-based payload for the exact 1412-FL base
# used during the physical BT metadata tests. Header formatting may differ;
# the payload hash is the compatibility lock.
EXPECTED_CLEAN_PAYLOAD_SHA256 = "9c4b3b051a9dd1705d2acd27658d25fb71a52f5c2a20f5595f4885016a3661a1"
ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

sys.path.insert(0, str(TOOLS))
from vbf_tool import Vbf, build  # noqa: E402


def run_tool(script: str, source: Path, destination: Path, can_id: int | None = None) -> None:
    command = [sys.executable, str(TOOLS / script), str(source), str(destination)]
    if can_id is not None:
        command.extend(["--canid", hex(can_id)])
    print("RUN:", " ".join(command))
    subprocess.run(command, check=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_vbf", type=Path, help="your own clean CS7T-14C026-CD.vbf")
    parser.add_argument(
        "output_vbf", type=Path, nargs="?",
        default=Path("CS7T-14C026-CD_BT_AUDIO_V5_2.vbf"),
        help="new VBF path; the input is never overwritten",
    )
    parser.add_argument(
        "--canid", type=lambda value: int(value, 0), default=DEFAULT_CAN_ID,
        help="Bluetooth metadata CAN ID; default 0x4B1, other IDs are experimental",
    )
    args = parser.parse_args()

    if not 0 <= args.canid <= 0x7FF:
        parser.error("CAN ID must be an 11-bit value")
    if not args.input_vbf.is_file():
        parser.error(f"input file does not exist: {args.input_vbf}")
    if args.input_vbf.resolve() == args.output_vbf.resolve():
        parser.error("input and output must be different; the source is never overwritten")

    source_vbf = Vbf(str(args.input_vbf))
    errors = source_vbf.check()
    if errors:
        raise SystemExit("Input VBF validation failed:\n  " + "\n  ".join(errors))
    if source_vbf.part_number != PART_NUMBER:
        raise SystemExit(
            f"Unexpected sw_part_number {source_vbf.part_number!r}; "
            f"expected {PART_NUMBER!r}"
        )
    if source_vbf.addr != BASE or source_vbf.length != 0xFB000:
        raise SystemExit(
            f"Unexpected code partition: addr=0x{source_vbf.addr:x}, "
            f"length=0x{source_vbf.length:x}"
        )
    payload_hash = hashlib.sha256(source_vbf.payload).hexdigest()
    if payload_hash != EXPECTED_CLEAN_PAYLOAD_SHA256:
        raise SystemExit(
            "Unsupported source payload.\n"
            f"  got:      {payload_hash}\n"
            f"  expected: {EXPECTED_CLEAN_PAYLOAD_SHA256}\n"
            "Do not bypass this check; this patch-kit targets one exact clean base."
        )

    print("Input:", args.input_vbf)
    print("Input SHA-256:", sha256(args.input_vbf))
    print("Payload SHA-256:", payload_hash)
    print("Part:", source_vbf.part_number)
    print("CAN metadata ID:", hex(args.canid))

    with tempfile.TemporaryDirectory(prefix="convers_bt_v5_2_") as work:
        workdir = Path(work)
        raw = workdir / "main.bin"
        received = workdir / "main_bt.bin"
        safe_renderer = workdir / "main_bt_render.bin"
        patched = workdir / "main_patched.bin"
        raw.write_bytes(source_vbf.payload)

        run_tool("apply_patch_v3.py", raw, received, args.canid)
        run_tool("apply_render.py", received, safe_renderer)
        run_tool("apply_layout_v5_2.py", safe_renderer, patched)

        args.output_vbf.parent.mkdir(parents=True, exist_ok=True)
        build(str(args.input_vbf), patched.read_bytes(), str(args.output_vbf))

    result = Vbf(str(args.output_vbf))
    errors = result.check()
    if errors:
        raise SystemExit("Output VBF validation failed:\n  " + "\n  ".join(errors))
    print("Output:", args.output_vbf)
    print("Output SHA-256:", sha256(args.output_vbf))
    print("VBF CRC16:", hex(result.crc16_stored))
    print("VBF CRC32:", hex(result.file_checksum))
    print("DONE: no flashing was performed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
