# Test report — BT Audio patch-kit V5.2

## Testy wykonane lokalnie

- `tools/apply_layout_v5_2.py --self-test` — PASS
- Python bytecode compilation for all tools and tests — PASS
- Full pipeline on a copy of the known clean 1412-FL payload — PASS
- Input VBF CRC validation — PASS
- Output VBF CRC16/CRC32 validation — PASS
- Source file is never overwritten — PASS
- Different payload hash is rejected before patching — PASS

Pipeline tested:

```text
clean VBF
  -> unpack 0x5000 payload
  -> Bluetooth CAN metadata patch v3
  -> title-buffer safety patch
  -> V5.2 fixed layout patch
  -> repack VBF
```

The known clean payload used in the test has SHA-256:

```text
9c4b3b051a9dd1705d2acd27658d25fb71a52f5c2a20f5595f4885016a3661a1
```

The reproducible test output in this workspace had SHA-256:

```text
bcc5eb7fde87d2f8908e31d58745c735e02516a022a2bd0c902bf349cbe79218
```

Its VBF checks were:

```text
CRC16: 0xf605
CRC32: 0x05c5caff
```

The output hash is an example for that exact input/template and should not be
used as a universal expected hash if the source VBF header differs.

## Test status on a physical cluster

The Bluetooth receive chain and the centering axis were previously confirmed
on the physical cluster with the earlier V5 build. V5.2 changes the field
order and makes the rows fixed when the album is absent. The clean-VBF
one-command pipeline still requires confirmation on the target vehicle.

## What these tests do not prove

They do not prove that an arbitrary vehicle broadcasts metadata on CAN `0x4B1`,
that a different firmware variant has the same addresses, or that a particular
flasher can recover an interrupted write. Those items require a vehicle-specific
test and a known recovery procedure.
