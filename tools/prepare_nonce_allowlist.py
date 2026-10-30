#!/usr/bin/env python3
"""Prepare the reviewed iPad5,1 RAM-only nonce allowlist change; never access USB."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

EXPECTED_INPUT = '8d6f8239cf6630fe33c23b3eac7efb1fd83b682e324375bf94163d38010840e2'
EXPECTED_OUTPUT = '42553f871d94486c5e0c778de673ec6f38abedc2762c7d3c83e0c1ebcd8c49c0'
BASE = 0x870000000
OFFSET = 0x54040

def prepare(data: bytes) -> tuple[bytes, dict]:
    if hashlib.sha256(data).hexdigest() != EXPECTED_INPUT:
        raise ValueError('Input is not the exact reviewed iBoot patcher output')
    if struct.unpack_from('<Q', data, 0x300)[0] != BASE:
        raise ValueError('Unexpected load address')
    pointer = struct.unpack_from('<Q', data, OFFSET)[0]
    start = pointer - BASE
    if data[start:data.index(0, start)] != b'pwr-path':
        raise ValueError('Unexpected write-allowlist entry')
    needle = b'\0com.apple.System.boot-nonce\0'
    if data.count(needle) != 1:
        raise ValueError('Missing or ambiguous nonce variable string')
    output = bytearray(data)
    struct.pack_into('<Q', output, OFFSET, BASE + data.index(needle) + 1)
    output = bytes(output)
    if hashlib.sha256(output).hexdigest() != EXPECTED_OUTPUT:
        raise ValueError('Output differs from the reviewed change')
    return output, {'input_sha256': EXPECTED_INPUT, 'output_sha256': EXPECTED_OUTPUT,
                    'offset': hex(OFFSET), 'before': data[OFFSET:OFFSET+8].hex(),
                    'after': output[OFFSET:OFFSET+8].hex(), 'device_access': False}

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    report_path = args.output.with_suffix(args.output.suffix + '.json')
    if args.output.exists() or report_path.exists():
        ap.error('Output already exists; refusing to overwrite')
    try:
        output, report = prepare(args.input.read_bytes())
        with args.output.open('xb') as f:
            f.write(output)
        with report_path.open('x') as f:
            f.write(json.dumps(report, indent=2)+'\n')
    except (OSError, ValueError) as error:
        ap.error(str(error))
    print(json.dumps(report, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
