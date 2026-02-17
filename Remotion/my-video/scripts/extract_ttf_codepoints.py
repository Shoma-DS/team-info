#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path


def be_u16(data: bytes, off: int) -> int:
    return struct.unpack_from(">H", data, off)[0]


def be_u32(data: bytes, off: int) -> int:
    return struct.unpack_from(">I", data, off)[0]


def parse_format_4(sub: bytes) -> set[int]:
    codepoints: set[int] = set()
    seg_count = be_u16(sub, 6) // 2
    end_code_off = 14
    start_code_off = end_code_off + 2 * seg_count + 2
    id_delta_off = start_code_off + 2 * seg_count
    id_range_off_off = id_delta_off + 2 * seg_count

    for i in range(seg_count):
        end_code = be_u16(sub, end_code_off + 2 * i)
        start_code = be_u16(sub, start_code_off + 2 * i)
        id_delta = be_u16(sub, id_delta_off + 2 * i)
        id_range_off = be_u16(sub, id_range_off_off + 2 * i)

        if start_code == 0xFFFF and end_code == 0xFFFF:
            continue
        if start_code > end_code:
            continue

        for c in range(start_code, end_code + 1):
            if id_range_off == 0:
                glyph = (c + id_delta) & 0xFFFF
            else:
                # Addressing per TrueType spec.
                ro_pos = id_range_off_off + 2 * i
                glyph_index_addr = ro_pos + id_range_off + 2 * (c - start_code)
                if glyph_index_addr + 2 > len(sub):
                    continue
                glyph_index = be_u16(sub, glyph_index_addr)
                if glyph_index == 0:
                    continue
                glyph = (glyph_index + id_delta) & 0xFFFF

            if glyph != 0:
                codepoints.add(c)

    return codepoints


def parse_format_12(sub: bytes) -> set[int]:
    codepoints: set[int] = set()
    n_groups = be_u32(sub, 12)
    groups_off = 16
    for i in range(n_groups):
        off = groups_off + i * 12
        if off + 12 > len(sub):
            break
        start_char = be_u32(sub, off)
        end_char = be_u32(sub, off + 4)
        start_glyph = be_u32(sub, off + 8)
        if start_glyph == 0:
            continue
        if start_char > end_char:
            continue
        for c in range(start_char, end_char + 1):
            codepoints.add(c)
    return codepoints


def parse_format_0(sub: bytes) -> set[int]:
    codepoints: set[int] = set()
    if len(sub) < 262:
        return codepoints
    for c in range(256):
        glyph = sub[6 + c]
        if glyph != 0:
            codepoints.add(c)
    return codepoints


def extract_codepoints(font_path: Path) -> set[int]:
    data = font_path.read_bytes()
    num_tables = be_u16(data, 4)
    table_dir = 12
    cmap_offset = None
    cmap_length = None

    for i in range(num_tables):
        rec = table_dir + i * 16
        tag = data[rec : rec + 4]
        if tag == b"cmap":
            cmap_offset = be_u32(data, rec + 8)
            cmap_length = be_u32(data, rec + 12)
            break

    if cmap_offset is None or cmap_length is None:
        raise RuntimeError("cmap table not found")

    cmap = data[cmap_offset : cmap_offset + cmap_length]
    n_subtables = be_u16(cmap, 2)
    points: set[int] = set()

    for i in range(n_subtables):
        rec = 4 + i * 8
        sub_off = be_u32(cmap, rec + 4)
        if sub_off >= len(cmap):
            continue
        fmt = be_u16(cmap, sub_off)
        if fmt == 4:
            points |= parse_format_4(cmap[sub_off:])
        elif fmt == 12:
            points |= parse_format_12(cmap[sub_off:])
        elif fmt == 0:
            points |= parse_format_0(cmap[sub_off:])

    return points


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: extract_ttf_codepoints.py <input.ttf> <output.json>")
        return 2

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    points = sorted(extract_codepoints(src))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps({"codepoints": points}, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(points)} codepoints -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
