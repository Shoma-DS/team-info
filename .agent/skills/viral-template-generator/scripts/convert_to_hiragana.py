#!/usr/bin/env python3
"""
convert_to_hiragana: script.md の台本テキストを読み仮名（ひらがな）に変換して
script_hiragana.md として保存する。VOICEVOX の読み間違い防止が目的。

変換の流れ:
  1. 数字を漢数字または読み仮名にプレ変換（例: 3選 → さんせん）
  2. pykakasi でひらがな変換
  3. 演出メモ・見出し行はそのまま保持

Usage:
  python3 convert_to_hiragana.py --script [script.mdの絶対パス]
  python3 convert_to_hiragana.py  # 自動検索
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import pykakasi
except ImportError:
    raise SystemExit(
        "pykakasi が見つかりません。pip install pykakasi でインストールしてください。"
    )

COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_repo_root

PROJECT_ROOT = get_repo_root()

# ─── 数字読み仮名テーブル ────────────────────────────────────────────────────

DIGIT_READ = {
    "0": "ぜろ", "1": "いち", "2": "に", "3": "さん",
    "4": "よん", "5": "ご", "6": "ろく", "7": "なな",
    "8": "はち", "9": "きゅう",
}

# 数字 + 単位の読み仮名（pykakasi が誤読しやすい組み合わせ）
NUMBER_UNIT_PATTERNS = [
    # 順番: 具体的なパターンを先に
    (r"(\d+)選",    lambda m: num_to_kana(m.group(1)) + "せん"),
    (r"(\d+)本",    lambda m: num_to_kana(m.group(1)) + "ほん"),
    (r"(\d+)人",    lambda m: num_to_kana(m.group(1)) + "にん"),
    (r"(\d+)枚",    lambda m: num_to_kana(m.group(1)) + "まい"),
    (r"(\d+)回",    lambda m: num_to_kana(m.group(1)) + "かい"),
    (r"(\d+)年",    lambda m: num_to_kana(m.group(1)) + "ねん"),
    (r"(\d+)秒",    lambda m: num_to_kana(m.group(1)) + "びょう"),
    (r"(\d+)分",    lambda m: num_to_kana(m.group(1)) + "ふん"),
    # 単独数字（文の中）
    (r"(?<![0-9])(\d+)(?![0-9選本人枚回年秒分])", lambda m: num_to_kana(m.group(1))),
]


def num_to_kana(s: str) -> str:
    """数字文字列をひらがな読みに変換する（例: '13' → 'じゅうさん'）"""
    n = int(s)
    if n == 0:
        return "ぜろ"
    if n < 10:
        return DIGIT_READ[s]

    result = ""
    if n >= 10000:
        result += num_to_kana(str(n // 10000)) + "まん"
        n %= 10000
    if n >= 1000:
        prefix = num_to_kana(str(n // 1000)) if n // 1000 > 1 else ""
        result += prefix + "せん"
        n %= 1000
    if n >= 100:
        prefix = num_to_kana(str(n // 100)) if n // 100 > 1 else ""
        result += prefix + "ひゃく"
        n %= 100
    if n >= 10:
        prefix = num_to_kana(str(n // 10)) if n // 10 > 1 else ""
        result += prefix + "じゅう"
        n %= 10
    if n > 0:
        result += DIGIT_READ[str(n)]
    return result


def preprocess_numbers(text: str) -> str:
    """数字+単位の組み合わせをひらがなに置換する"""
    for pattern, replacer in NUMBER_UNIT_PATTERNS:
        text = re.sub(pattern, replacer, text)
    return text


# ─── ひらがな変換 ─────────────────────────────────────────────────────────────

def to_hiragana(text: str, kks: pykakasi.kakasi) -> str:
    """テキスト全体をひらがなに変換する"""
    result = kks.convert(text)
    return "".join(item["hira"] for item in result)


def convert_line(line: str, kks: pykakasi.kakasi) -> str:
    """
    1行を変換する。
    - Markdown 見出し（##）・区切り（---）・空行はそのまま返す
    - それ以外の行は数字変換 → ひらがな変換
    """
    stripped = line.strip()
    # 見出し・区切り行はそのまま
    if stripped.startswith("#") or stripped == "---" or stripped == "":
        return line

    # 数字を先にひらがな化
    preprocessed = preprocess_numbers(stripped)

    # pykakasi でひらがな変換
    hira = to_hiragana(preprocessed, kks)

    # インデントを保持
    indent = len(line) - len(line.lstrip())
    return " " * indent + hira


# ─── ファイル単位処理 ─────────────────────────────────────────────────────────

def convert_script(script_path: Path) -> Path:
    """script.md を読み込んでひらがな版 script_hiragana.md を生成する"""
    kks = pykakasi.kakasi()
    text = script_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    converted_lines = []
    in_meta = True  # ファイル先頭のメタ情報（#見出し、プラットフォームなど）

    for line in lines:
        stripped = line.strip()

        # ファイル先頭のメタ情報ブロック（最初の --- まで）はそのまま
        if in_meta:
            converted_lines.append(line)
            if stripped == "---":
                in_meta = False
            continue

        # 演出メモセクションはそのまま
        if stripped.startswith("## 演出メモ"):
            converted_lines.append(line)
            continue

        converted_lines.append(convert_line(line, kks))

    output_path = script_path.with_name("script_hiragana.md")
    output_path.write_text("".join(converted_lines), encoding="utf-8")
    return output_path


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="script.md をひらがな読み仮名に変換")
    parser.add_argument("--script", "-s", type=Path, required=False,
                        help="script.md の絶対パス（省略時は自動検索）")
    args = parser.parse_args()

    if args.script:
        script_path = args.script
    else:
        candidates = [
            c for c in PROJECT_ROOT.rglob("script.md")
            if "node_modules" not in str(c) and "script_hiragana" not in str(c)
        ]
        if not candidates:
            raise SystemExit("script.md が見つかりません。--script で指定してください。")
        if len(candidates) == 1:
            script_path = candidates[0]
            print(f"台本: {script_path}")
        else:
            for i, c in enumerate(candidates):
                print(f"  [{i}] {c}")
            idx = int(input("番号を選択: "))
            script_path = candidates[idx]

    print(f"変換中: {script_path.name} → script_hiragana.md")
    output = convert_script(script_path)
    print(f"完了: {output}")
    print("\n⚠ 確認してください:")
    print("  固有名詞・人名の読みが正しいか script_hiragana.md を開いて確認し、")
    print("  誤りがあれば手動で修正してから音源化してください。")

    # プレビュー（最初の30行）
    preview_lines = output.read_text(encoding="utf-8").splitlines()[:30]
    print("\n--- プレビュー ---")
    for l in preview_lines:
        print(l)


if __name__ == "__main__":
    main()
