#!/usr/bin/env python3
"""
split_subtitles: BudouX で subtitles.json の長いセグメントを文節区切りで分割する。

モード:
  --mode newline  : 1セグメント内で \n 折り返し（デフォルト）
                    → SubtitleTrack で white-space: pre-wrap にする
  --mode split    : 長いセグメントを複数の時間セグメントに分割
                    → subtitles.json のエントリ数が増える

Usage:
  python3 split_subtitles.py --input [subtitles.json] --output [out.json]
  python3 split_subtitles.py --input [subtitles.json] --output [out.json] --mode split
  python3 split_subtitles.py --input [subtitles.json]   # 上書き（バックアップ自動作成）
"""
import argparse
import json
import shutil
from pathlib import Path

try:
    import budoux
except ImportError:
    raise SystemExit(
        "budoux が見つかりません。team_info_runtime.py build-remotion-python で Docker ランタイムを再ビルドしてください。"
    )

PARSER = budoux.load_default_japanese_parser()

# 1行あたりの推奨最大文字数（これを超えたら折り返し or 分割対象）
LINE_MAX = 13


def group_chunks_to_lines(chunks: list[str], line_max: int) -> list[str]:
    """
    BudouX のチャンクリストを line_max 以内の行に結合する。
    例: ["ピアスに", "タトゥー、", "過激な", "役柄を"] → ["ピアスに", "タトゥー、過激な役柄を"]
    """
    lines: list[str] = []
    current = ""
    for chunk in chunks:
        if current and len(current) + len(chunk) > line_max:
            lines.append(current)
            current = chunk
        else:
            current += chunk
    if current:
        lines.append(current)
    return lines


def process_newline_mode(segments: list[dict], line_max: int = LINE_MAX) -> list[dict]:
    """
    各セグメントのテキストを \n 折り返しに変換する（タイミング変更なし）。
    line_max 以下の場合はそのまま。
    """
    result = []
    for seg in segments:
        text = seg["text"]
        if len(text) <= line_max:
            result.append(seg)
            continue

        chunks = PARSER.parse(text)
        lines = group_chunks_to_lines(chunks, line_max)

        new_seg = dict(seg)
        new_seg["text"] = "\n".join(lines)
        result.append(new_seg)
    return result


def process_split_mode(segments: list[dict], line_max: int = LINE_MAX) -> list[dict]:
    """
    長いセグメントを複数の時間セグメントに分割する。
    各サブセグメントの尺は文字数比で案分する。
    line_max 以下のセグメントはそのまま。
    """
    result = []
    new_id = 1
    for seg in segments:
        text = seg["text"]
        if len(text) <= line_max:
            new_seg = dict(seg)
            new_seg["id"] = new_id
            result.append(new_seg)
            new_id += 1
            continue

        chunks = PARSER.parse(text)
        lines = group_chunks_to_lines(chunks, line_max)

        if len(lines) == 1:
            new_seg = dict(seg)
            new_seg["id"] = new_id
            result.append(new_seg)
            new_id += 1
            continue

        fps = seg.get("fps", 30)
        total_chars = sum(len(l) for l in lines)
        total_frames = seg["to_frame"] - seg["from_frame"]
        total_duration = seg["to_time"] - seg["from_time"]

        cur_frame = seg["from_frame"]
        cur_time = seg["from_time"]

        for i, line in enumerate(lines):
            ratio = len(line) / total_chars
            dur_frames = round(total_frames * ratio)
            dur_time = total_duration * ratio

            # 最後のサブセグメントは端数を吸収
            if i == len(lines) - 1:
                end_frame = seg["to_frame"]
                end_time = seg["to_time"]
            else:
                end_frame = cur_frame + dur_frames
                end_time = round(cur_time + dur_time, 3)

            sub = {
                "id": new_id,
                "section": seg["section"],
                "from_time": round(cur_time, 3),
                "to_time": round(end_time, 3),
                "from_frame": cur_frame,
                "to_frame": end_frame,
                "text": line,
            }
            result.append(sub)
            new_id += 1
            cur_frame = end_frame
            cur_time = end_time

    return result


def main():
    parser = argparse.ArgumentParser(description="BudouX で字幕を文節区切り分割")
    parser.add_argument("--input", "-i", type=Path, required=False,
                        help="入力 subtitles.json のパス")
    parser.add_argument("--output", "-o", type=Path, required=False,
                        help="出力パス（省略時は入力ファイルを上書き＋バックアップ）")
    parser.add_argument("--mode", choices=["newline", "split"], default="newline",
                        help="newline: \\n折り返し (default) / split: 時間分割")
    parser.add_argument("--line-max", type=int, default=LINE_MAX,
                        help=f"1行の最大文字数 (default: {LINE_MAX})")
    args = parser.parse_args()

    # 入力ファイルの決定
    if args.input:
        input_path = args.input
    else:
        # インタラクティブ: プロジェクトルート配下の subtitles.json を探す
        from pathlib import Path as P
        candidates = list(P(__file__).parents[3].rglob("subtitles.json"))
        candidates = [c for c in candidates if "node_modules" not in str(c)]
        if not candidates:
            raise SystemExit("subtitles.json が見つかりません。--input で指定してください。")
        if len(candidates) == 1:
            input_path = candidates[0]
            print(f"対象: {input_path}")
        else:
            for i, c in enumerate(candidates):
                print(f"  [{i}] {c}")
            idx = int(input("番号を選択: "))
            input_path = candidates[idx]

    output_path = args.output or input_path

    data = json.loads(input_path.read_text(encoding="utf-8"))
    segments = data["segments"]

    line_max = args.line_max

    print(f"モード: {args.mode} / 1行最大: {LINE_MAX}文字 / 入力セグメント数: {len(segments)}")

    if args.mode == "newline":
        new_segments = process_newline_mode(segments, line_max)
    else:
        new_segments = process_split_mode(segments, line_max)

    data["segments"] = new_segments

    # バックアップ（上書きの場合のみ）
    if output_path == input_path:
        backup = input_path.with_suffix(".backup.json")
        shutil.copy(input_path, backup)
        print(f"バックアップ: {backup}")

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"出力: {output_path}  ({len(new_segments)} セグメント)")

    # 変更があったセグメントを表示
    for orig, new in zip(segments, new_segments[:len(segments)]):
        if orig["text"] != new["text"]:
            print(f"  [{orig['id']}] {orig['text']!r}")
            print(f"       → {new['text']!r}")


if __name__ == "__main__":
    main()
