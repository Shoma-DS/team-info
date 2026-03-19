#!/usr/bin/env python3
"""
split_subtitles: GiNZA で subtitles.json の文/文節を解析し、字幕を見やすく再配置する。

モード:
  --mode newline  : 文単位を優先して改行を入れ、非フックで3行以上になる場合は
                    2行以内に収めて次の字幕セグメントへ持ち越す（デフォルト）
  --mode split    : 各行を独立した時間セグメントへ分割する
  --mode card     : 参照テンプレ向けの短い字幕カードへ再配置する
"""
import argparse
import json
import re
import shutil
from pathlib import Path

try:
    import ginza
    import spacy
except ImportError:
    raise SystemExit(
        "GiNZA / spaCy が見つかりません。setup/requirements.txt を更新後、"
        "team_info_runtime.py build-remotion-python で Docker ランタイムを再ビルドしてください。"
    )

try:
    NLP = spacy.load("ja_ginza")
except OSError as exc:
    raise SystemExit(
        "ja_ginza モデルが見つかりません。setup/requirements.txt を更新後、"
        "team_info_runtime.py build-remotion-python で Docker ランタイムを再ビルドしてください。"
    ) from exc

LINE_MAX = 13
MAX_LINES = 2
HOOK_SECTION = "hook"
CARD_LINE_MAX = 7
HOOK_CARD_LINE_MAX = 6
NAME_CARD_PATTERN = re.compile(r"^\s*([1-3])人目は(.+?)\s*[。.!！?？]*\s*$")


def _compact_text(text: str) -> str:
    return text.replace("\r", "").replace("\n", "").strip()


def _normalize_name_card_text(text: str) -> str:
    compact = _compact_text(text)
    match = NAME_CARD_PATTERN.match(compact)
    if not match:
        return compact

    number = match.group(1)
    name = match.group(2).strip().strip("「」『』")
    return f"{number}.{name}"


def _is_name_card_text(text: str) -> bool:
    return bool(NAME_CARD_PATTERN.match(_compact_text(text)))


def _char_fallback(text: str, line_max: int) -> list[str]:
    compact = _compact_text(text)
    if not compact:
        return []
    return [compact[i:i + line_max] for i in range(0, len(compact), line_max)]


def _split_oversized_bunsetu(span, line_max: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for token in span:
        piece = token.text
        if not piece.strip():
            continue
        if len(piece) > line_max:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(_char_fallback(piece, line_max))
            continue
        if current and len(current) + len(piece) > line_max:
            pieces.append(current)
            current = piece
        else:
            current += piece
    if current:
        pieces.append(current)
    return pieces or _char_fallback(span.text, line_max)


def _sentence_chunks(text: str, line_max: int) -> list[list[str]]:
    compact = _compact_text(text)
    if not compact:
        return []

    doc = NLP(compact)
    sentence_chunks: list[list[str]] = []
    for sent in doc.sents:
        sent_text = sent.text.strip()
        if not sent_text:
            continue

        chunks: list[str] = []
        for bunsetu_span in ginza.bunsetu_spans(sent):
            span_text = bunsetu_span.text.strip()
            if not span_text:
                continue
            if len(span_text) <= line_max:
                chunks.append(span_text)
            else:
                chunks.extend(_split_oversized_bunsetu(bunsetu_span, line_max))

        sentence_chunks.append(chunks or _char_fallback(sent_text, line_max))

    return sentence_chunks or [_char_fallback(compact, line_max)]


def group_chunks_to_lines(chunks: list[str], line_max: int) -> list[str]:
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


def _sentence_line_groups(text: str, line_max: int) -> list[list[str]]:
    return [group_chunks_to_lines(chunks, line_max) for chunks in _sentence_chunks(text, line_max)]


def _pack_newline_groups(sentence_line_groups: list[list[str]], max_lines: int) -> list[str]:
    result: list[str] = []
    current: list[str] = []

    for lines in sentence_line_groups:
        if not lines:
            continue

        if current and len(current) + len(lines) <= max_lines:
            current.extend(lines)
            continue

        if current:
            result.append("\n".join(current))
            current = []

        if len(lines) <= max_lines:
            current = list(lines)
            continue

        start = 0
        while start + max_lines < len(lines):
            result.append("\n".join(lines[start:start + max_lines]))
            start += max_lines
        current = list(lines[start:])

    if current:
        result.append("\n".join(current))

    return result or [""]


def _newline_texts(seg: dict, line_max: int, max_lines: int) -> list[str]:
    if str(seg.get("section", "")) == HOOK_SECTION:
        return [str(seg["text"])]

    groups = _sentence_line_groups(str(seg["text"]), line_max)
    return _pack_newline_groups(groups, max_lines)


def _split_texts(seg: dict, line_max: int) -> list[str]:
    groups = _sentence_line_groups(str(seg["text"]), line_max)
    lines = [line for group in groups for line in group]
    return lines or [str(seg["text"])]


def _text_weight(text: str) -> int:
    return max(1, len(text.replace("\n", "")))


def _pack_card_texts(chunks: list[str], line_max: int, max_lines: int) -> list[str]:
    cards: list[str] = []
    current_lines: list[str] = []

    for raw_chunk in chunks:
        chunk = raw_chunk.strip()
        if not chunk:
            continue

        if not current_lines:
            current_lines = [chunk]
            continue

        last_line = current_lines[-1]
        if len(last_line) + len(chunk) <= line_max:
            current_lines[-1] = last_line + chunk
            continue

        if len(current_lines) < max_lines:
            current_lines.append(chunk)
            continue

        cards.append("\n".join(current_lines))
        current_lines = [chunk]

    if current_lines:
        cards.append("\n".join(current_lines))

    return cards or [""]


def _card_texts(
    seg: dict,
    line_max: int,
    max_lines: int,
    hook_line_max: int,
) -> list[str]:
    raw_text = str(seg["text"])
    if str(seg.get("section", "")) == HOOK_SECTION:
        hook_groups = _sentence_chunks(raw_text, hook_line_max)
        hook_lines = [line for group in hook_groups for line in group_chunks_to_lines(group, hook_line_max)]
        return ["\n".join(hook_lines or [_compact_text(raw_text)])]

    if _is_name_card_text(raw_text):
        return [_normalize_name_card_text(raw_text)]

    sentence_groups = _sentence_chunks(raw_text, line_max)
    cards: list[str] = []
    for chunks in sentence_groups:
        cards.extend(_pack_card_texts(chunks, line_max, max_lines))

    return cards or [_compact_text(raw_text)]


def _resegment(seg: dict, texts: list[str], start_id: int) -> tuple[list[dict], int]:
    if not texts:
        return [], start_id

    weights = [_text_weight(text) for text in texts]
    total_weight = sum(weights)
    original_from_frame = int(seg["from_frame"])
    original_to_frame = int(seg["to_frame"])
    original_from_time = float(seg["from_time"])
    original_to_time = float(seg["to_time"])

    cur_frame = original_from_frame
    cur_time = original_from_time
    remaining_frames = original_to_frame - original_from_frame
    remaining_time = original_to_time - original_from_time
    remaining_weight = total_weight

    result: list[dict] = []
    for index, text in enumerate(texts):
        weight = weights[index]
        is_last = index == len(texts) - 1
        if is_last:
            end_frame = original_to_frame
            end_time = original_to_time
        else:
            ratio = weight / remaining_weight if remaining_weight else 0
            remaining_segments = len(texts) - index - 1
            dur_frames = max(1, round(remaining_frames * ratio))
            dur_frames = min(dur_frames, max(1, remaining_frames - remaining_segments))
            dur_time = remaining_time * ratio
            end_frame = cur_frame + dur_frames
            end_time = round(cur_time + dur_time, 3)

        new_seg = dict(seg)
        new_seg["id"] = start_id
        new_seg["text"] = text
        new_seg["from_frame"] = cur_frame
        new_seg["to_frame"] = end_frame
        new_seg["from_time"] = round(cur_time, 3)
        new_seg["to_time"] = round(end_time, 3)
        result.append(new_seg)

        start_id += 1
        cur_frame = end_frame
        cur_time = end_time
        remaining_frames = original_to_frame - cur_frame
        remaining_time = original_to_time - cur_time
        remaining_weight -= weight

    return result, start_id


def process_newline_mode(
    segments: list[dict],
    line_max: int = LINE_MAX,
    max_lines: int = MAX_LINES,
) -> list[dict]:
    result: list[dict] = []
    new_id = 1
    for seg in segments:
        texts = _newline_texts(seg, line_max, max_lines)
        expanded, new_id = _resegment(seg, texts, new_id)
        result.extend(expanded)
    return result


def process_split_mode(segments: list[dict], line_max: int = LINE_MAX) -> list[dict]:
    result: list[dict] = []
    new_id = 1
    for seg in segments:
        texts = _split_texts(seg, line_max)
        expanded, new_id = _resegment(seg, texts, new_id)
        result.extend(expanded)
    return result


def process_card_mode(
    segments: list[dict],
    line_max: int = CARD_LINE_MAX,
    max_lines: int = MAX_LINES,
    hook_line_max: int = HOOK_CARD_LINE_MAX,
) -> list[dict]:
    result: list[dict] = []
    new_id = 1
    for seg in segments:
        texts = _card_texts(seg, line_max, max_lines, hook_line_max)
        expanded, new_id = _resegment(seg, texts, new_id)
        result.extend(expanded)
    return result


def main():
    parser = argparse.ArgumentParser(description="GiNZA で字幕を文/文節ベースに再配置")
    parser.add_argument("--input", "-i", type=Path, required=False,
                        help="入力 subtitles.json のパス")
    parser.add_argument("--output", "-o", type=Path, required=False,
                        help="出力パス（省略時は入力ファイルを上書き＋バックアップ）")
    parser.add_argument("--mode", choices=["newline", "split", "card"], default="newline",
                        help="newline: 2行以内に整理 / split: 各行を時間分割 / card: 短い2行カードへ再配置")
    parser.add_argument("--line-max", type=int, default=LINE_MAX,
                        help=f"1行の最大文字数 (default: {LINE_MAX})")
    parser.add_argument("--max-lines", type=int, default=MAX_LINES,
                        help=f"newline モード時の最大行数 (default: {MAX_LINES})")
    parser.add_argument("--hook-line-max", type=int, default=HOOK_CARD_LINE_MAX,
                        help=f"card モード時の hook 1行最大文字数 (default: {HOOK_CARD_LINE_MAX})")
    args = parser.parse_args()

    if args.input:
        input_path = args.input
    else:
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

    print(
        f"モード: {args.mode} / 1行最大: {args.line_max}文字 / "
        f"最大行数: {args.max_lines} / 入力セグメント数: {len(segments)}"
    )

    if args.mode == "newline":
        new_segments = process_newline_mode(segments, args.line_max, args.max_lines)
    elif args.mode == "card":
        card_line_max = args.line_max if args.line_max != LINE_MAX else CARD_LINE_MAX
        new_segments = process_card_mode(segments, card_line_max, args.max_lines, args.hook_line_max)
    else:
        new_segments = process_split_mode(segments, args.line_max)

    data["segments"] = new_segments

    if output_path == input_path:
        backup = input_path.with_suffix(".backup.json")
        shutil.copy(input_path, backup)
        print(f"バックアップ: {backup}")

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"出力: {output_path}  ({len(new_segments)} セグメント)")
    if len(new_segments) != len(segments):
        print(f"セグメント数変化: {len(segments)} -> {len(new_segments)}")


if __name__ == "__main__":
    main()
