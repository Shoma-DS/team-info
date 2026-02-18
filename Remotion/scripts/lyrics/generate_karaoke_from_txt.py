#!/usr/bin/env python3
import argparse
import json
import math
import re
from pathlib import Path


HEADER_RE = re.compile(r"^[\[\(【].*[\]\)】]$")
TOKEN_RE = re.compile(r"[A-Za-z0-9'’]+|[一-龥々〆〤ぁ-んァ-ヶー]+|[^\s]")


def parse_lyrics(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    items = []
    current_label = "Verse"
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if HEADER_RE.match(line):
            current_label = line.strip("[]()【】")
            continue
        items.append({"label": current_label or "Verse", "text": line})
    return items


def visible_len(text: str) -> int:
    return len(re.sub(r"[\s\u3000]", "", text))


def tokenize(text: str):
    return TOKEN_RE.findall(text)


def to_lrc_timestamp(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"[{m:02d}:{s:02d}.{cs:02d}]"


def allocate_durations(weights, available, min_duration):
    base = [max(min_duration, available * (w / sum(weights))) for w in weights]
    total = sum(base)
    if total <= available:
        return base

    floor_sum = min_duration * len(base)
    if floor_sum >= available:
        even = available / len(base)
        return [even for _ in base]

    flex = [d - min_duration for d in base]
    shrink_target = total - available
    flex_total = sum(flex)
    if flex_total <= 0:
        even = available / len(base)
        return [even for _ in base]

    out = []
    for d, f in zip(base, flex):
        out.append(d - shrink_target * (f / flex_total))
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Generate rough karaoke LRC and lyric_animation_data.json from lyrics txt."
    )
    parser.add_argument("lyrics_txt")
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--lrc-output", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--intro-seconds", type=float, default=4.0)
    parser.add_argument("--outro-seconds", type=float, default=2.5)
    parser.add_argument("--min-line-seconds", type=float, default=1.8)
    args = parser.parse_args()

    lyrics_path = Path(args.lyrics_txt)
    entries = parse_lyrics(lyrics_path)
    if not entries:
        raise SystemExit("No lyric lines found.")

    intro = max(0.0, args.intro_seconds)
    outro = max(0.0, args.outro_seconds)
    total_duration = max(0.0, args.duration)
    body_duration = max(0.1, total_duration - intro - outro)

    weights = [max(4, visible_len(e["text"])) for e in entries]
    line_durations = allocate_durations(weights, body_duration, args.min_line_seconds)

    lrc_lines = []
    json_items = []
    cursor = intro

    if intro > 0:
        json_items.append(
            {
                "time": round(0.0, 2),
                "duration": round(intro, 2),
                "text": "(イントロ)",
                "label": "Intro",
                "emotion": "",
                "words": [{"word": "(イントロ)", "start": 0.0, "end": round(intro, 2)}],
                "animation": {
                    "in": "FadeInSlow",
                    "out": "FadeOut",
                    "props": {"inDurationFrames": 10, "outDurationFrames": 8},
                },
            }
        )

    for entry, line_dur in zip(entries, line_durations):
        text = entry["text"]
        label = entry["label"]
        line_dur = max(0.25, line_dur)
        lrc_lines.append(f"{to_lrc_timestamp(cursor)}{text}")

        tokens = tokenize(text)
        token_weights = [max(1, visible_len(t)) for t in tokens] if tokens else [1]
        token_total = sum(token_weights)
        word_cursor = 0.0
        words = []
        for token, w in zip(tokens, token_weights):
            d = line_dur * (w / token_total)
            start = word_cursor
            end = min(line_dur, word_cursor + d)
            words.append(
                {
                    "word": token,
                    "start": round(start, 2),
                    "end": round(end, 2),
                }
            )
            word_cursor = end

        json_items.append(
            {
                "time": round(cursor, 2),
                "duration": round(line_dur, 2),
                "text": text,
                "label": label,
                "emotion": "",
                "words": words,
                "animation": {
                    "in": "Karaoke",
                    "out": "FadeOut",
                    "props": {"inDurationFrames": 10, "outDurationFrames": 8},
                },
            }
        )
        cursor += line_dur

    remaining = max(0.0, total_duration - cursor)
    if remaining > 0.2:
        json_items.append(
            {
                "time": round(cursor, 2),
                "duration": round(remaining, 2),
                "text": "(アウトロ)",
                "label": "Outro",
                "emotion": "",
                "words": [{"word": "(アウトロ)", "start": 0.0, "end": round(remaining, 2)}],
                "animation": {
                    "in": "FadeInSlow",
                    "out": "FadeOut",
                    "props": {"inDurationFrames": 10, "outDurationFrames": 8},
                },
            }
        )

    lrc_path = Path(args.lrc_output)
    lrc_path.write_text("\n".join(lrc_lines) + "\n", encoding="utf-8")

    json_path = Path(args.json_output)
    json_path.write_text(
        json.dumps(json_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote LRC: {lrc_path}")
    print(f"Wrote JSON: {json_path}")


if __name__ == "__main__":
    main()
