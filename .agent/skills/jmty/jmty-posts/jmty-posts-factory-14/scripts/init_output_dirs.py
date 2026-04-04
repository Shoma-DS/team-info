#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


TEMPLATE = """# タイトル

## 本文

## 仕事内容詳細

## 募集概要
- 職種:
- 雇用形態:
- 勤務地:
- 勤務時間:
- 給与:
- 休日:
- 応募条件:

## 応募導線
気になる方は公式LINEからご連絡ください。  
【公式LINEURL】
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root")
    args = parser.parse_args()

    output_root = Path(args.output_root).expanduser()
    output_root.mkdir(parents=True, exist_ok=True)

    for index in range(1, 15):
        output_file = output_root / f"post{index:02d}.md"
        if not output_file.exists():
            output_file.write_text(TEMPLATE, encoding="utf-8")

    print(f"Created 14 post files under: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

