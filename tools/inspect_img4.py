#!/usr/bin/env python3
"""Read-only IMG4 structure/nonce inspection. No signature or boot verification."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys

class FormatError(ValueError):
    pass

@dataclass(frozen=True)
class Node:
    tag: bytes
    value: bytes
    raw: bytes
    children: tuple['Node', ...]


def parse(data: bytes, *, allow_trailing: bool = False) -> Node:
    if not data or len(data) > 64 * 1024 * 1024:
        raise FormatError('Expected 1..64 MiB of DER input')
    count = 0
    def read(start: int, limit: int, depth: int) -> tuple[Node, int]:
        nonlocal count
        count += 1
        if depth > 64 or count > 20000 or start >= limit:
            raise FormatError('DER nesting/node limit or truncated tag')
        pos = start
        first = data[pos]
        pos += 1
        if first & 31 == 31:
            for _ in range(9):
                if pos >= limit:
                    raise FormatError('Truncated DER tag')
                byte = data[pos]
                pos += 1
                if not byte & 128:
                    break
            else:
                raise FormatError('DER tag too large')
        tag = data[start:pos]
        if pos >= limit:
            raise FormatError('Missing DER length')
        length = data[pos]
        pos += 1
        if length & 128:
            width = length & 127
            if not width or width > 8 or pos + width > limit:
                raise FormatError('Invalid DER length')
            if data[pos] == 0:
                raise FormatError('Nonminimal DER length')
            length = int.from_bytes(data[pos:pos + width], 'big')
            pos += width
            if length < 128:
                raise FormatError('Nonminimal DER length')
        end = pos + length
        if end > limit:
            raise FormatError('Truncated DER value')
        children = []
        if first & 32:
            at = pos
            while at < end:
                child, at = read(at, end, depth + 1)
                children.append(child)
        return Node(tag, data[pos:end], data[start:end], tuple(children)), end
    root, end = read(0, len(data), 0)
    if end != len(data) and not allow_trailing:
        raise FormatError('Trailing bytes; use --allow-trailing for a media dump')
    return root


def named_octets(root: Node, name: bytes, length: int) -> bytes | None:
    values = []
    def walk(node: Node) -> None:
        children = node.children
        if len(children) >= 2 and children[0].tag == b'\x16' and children[0].value == name:
            value = children[1]
            if value.tag == b'\x04' and len(value.value) == length:
                values.append(value.value)
        for child in children:
            walk(child)
    walk(root)
    if len(values) > 1:
        raise FormatError(f'Duplicate/ambiguous {name.decode()} octet property')
    return values[0] if values else None


def inspect(data: bytes, *, allow_trailing: bool = False) -> tuple[dict, bytes]:
    root = parse(data, allow_trailing=allow_trailing)
    parts = root.children
    if root.tag != b'\x30' or len(parts) not in (3, 4):
        raise FormatError('Expected IMG4 sequence with payload, manifest and optional restore info')
    if parts[0].tag != b'\x16' or parts[0].value != b'IMG4':
        raise FormatError('Not an IMG4 image')
    payload = parts[1]
    if payload.tag != b'\x30' or len(payload.children) < 4 or payload.children[0].value != b'IM4P':
        raise FormatError('Missing IM4P payload')
    kind = payload.children[1]
    if kind.tag != b'\x16' or len(kind.value) != 4:
        raise FormatError('Invalid component type')
    wrapper = parts[2]
    if wrapper.tag != b'\xa0' or len(wrapper.children) != 1:
        raise FormatError('Missing/ambiguous IM4M wrapper')
    manifest = wrapper.children[0]
    if not manifest.children or manifest.children[0].value != b'IM4M':
        raise FormatError('Missing IM4M')
    bnch = named_octets(manifest, b'BNCH', 20)
    bncn = None
    if len(parts) == 4:
        restore = parts[3]
        if restore.tag != b'\xa1' or len(restore.children) != 1:
            raise FormatError('Invalid IM4R wrapper')
        restore = restore.children[0]
        if not restore.children or restore.children[0].value != b'IM4R':
            raise FormatError('Missing IM4R')
        bncn = named_octets(restore, b'BNCN', 8)
    available = bncn is not None and bnch is not None
    report = {
        'component_type': kind.value.decode('ascii'),
        'image_sha256': hashlib.sha256(root.raw).hexdigest(),
        'im4p_sha256': hashlib.sha256(payload.raw).hexdigest(),
        'im4m_sha1': hashlib.sha1(manifest.raw).hexdigest(),
        'bncn': bncn.hex() if bncn is not None else None,
        'generator_uint64_le': f'0x{int.from_bytes(bncn, "little"):016x}' if bncn is not None else None,
        'sha1_bncn': hashlib.sha1(bncn).hexdigest() if bncn is not None else None,
        'bnch_20_bytes': bnch.hex() if bnch is not None else None,
        'nonce_relationship_matches': hashlib.sha1(bncn).digest() == bnch if available else None,
        'signature_verified': False,
        'boot_verified': False,
        'trailing_bytes': len(data) - len(root.raw),
    }
    return report, payload.raw


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image', type=Path)
    ap.add_argument('--require-nonce', action='store_true')
    ap.add_argument('--allow-trailing', action='store_true')
    ap.add_argument('--stock-im4p', type=Path)
    ap.add_argument('--expect-ticket-sha1')
    args = ap.parse_args()
    try:
        report, payload = inspect(args.image.read_bytes(), allow_trailing=args.allow_trailing)
        passed = report['nonce_relationship_matches'] is not False
        if args.require_nonce:
            passed = report['nonce_relationship_matches'] is True
        if args.stock_im4p:
            report['stock_im4p_matches'] = payload == args.stock_im4p.read_bytes()
            passed = passed and report['stock_im4p_matches']
        if args.expect_ticket_sha1:
            report['expected_ticket_matches'] = report['im4m_sha1'] == args.expect_ticket_sha1.lower()
            passed = passed and report['expected_ticket_matches']
        report['requested_structural_checks_passed'] = bool(passed)
        print(json.dumps(report, indent=2))
        return 0 if passed else 2
    except (OSError, ValueError) as error:
        print(f'Inspection failed: {error}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
