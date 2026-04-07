#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path


LRC_RE = re.compile(r"^\[(\d{2}):(\d{2})[.:](\d{2})\](.*)$")
HEADER_RE = re.compile(r"^[\[【](.+)[\]】]$")
TOKEN_RE = re.compile(r"[A-Za-z0-9'’]+|[一-龥々〆〤ぁ-んァ-ヶー]+|[^\s]")


def normalize_text(s: str) -> str:
    return re.sub(r"[\s\u3000,，.。!！?？]", "", s)


def tokenize(text: str):
    return TOKEN_RE.findall(text)


def visible_len(text: str) -> int:
    return len(re.sub(r"[\s\u3000]", "", text))


def parse_lrc(path: Path):
    entries = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = LRC_RE.match(line)
        if not m:
            continue
        mm = int(m.group(1))
        ss = int(m.group(2))
        xx = int(m.group(3))
        text = m.group(4).strip()
        t = mm * 60 + ss + (xx / 100.0)
        entries.append({"time": t, "text": text})
    return entries


def parse_txt_labels(path: Path):
    labels = []
    current = "Verse"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        hm = HEADER_RE.match(line)
        if hm:
            current = hm.group(1).strip() or "Verse"
            continue
        labels.append({"text": line, "label": current})
    return labels


def map_labels(lrc_entries, txt_lines):
    mapped = []
    j = 0
    for e in lrc_entries:
        label = "Verse"
        lrc_norm = normalize_text(e["text"])
        while j < len(txt_lines):
            txt_norm = normalize_text(txt_lines[j]["text"])
            if lrc_norm == txt_norm:
                label = txt_lines[j]["label"]
                j += 1
                break
            j += 1
        mapped.append({**e, "label": label})
    return mapped


def get_audio_duration(audio_path: Path):
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        out = subprocess.check_output(cmd, text=True).strip()
        return float(out)
    except Exception:
        return None


def build_json(entries, audio_duration):
    out = []
    for i, e in enumerate(entries):
        t = e["time"]
        if i + 1 < len(entries):
            duration = max(0.2, entries[i + 1]["time"] - t)
        elif audio_duration is not None:
            duration = max(0.2, audio_duration - t)
        else:
            duration = 3.0

        words = tokenize(e["text"])
        if not words:
            words = [e["text"]]
        weights = [max(1, visible_len(w)) for w in words]
        total = sum(weights)
        cursor = 0.0
        word_items = []
        for w, wt in zip(words, weights):
            wdur = duration * (wt / total)
            start = round(cursor, 2)
            end = round(min(duration, cursor + wdur), 2)
            word_items.append({"word": w, "start": start, "end": end})
            cursor += wdur

        out.append(
            {
                "time": round(t, 2),
                "duration": round(duration, 2),
                "text": e["text"],
                "label": e["label"],
                "emotion": "",
                "words": word_items,
                "animation": {
                    "in": "Karaoke",
                    "out": "FadeOut",
                    "props": {"inDurationFrames": 10, "outDurationFrames": 8},
                },
            }
        )
    return out


def main():
    parser = argparse.ArgumentParser(description="Convert LRC (+lyrics txt labels) to lyric_animation_data.json")
    parser.add_argument("--lrc", required=True)
    parser.add_argument("--lyrics-txt", required=True)
    parser.add_argument("--audio", required=False)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    lrc_entries = parse_lrc(Path(args.lrc))
    if not lrc_entries:
        raise SystemExit("No valid LRC entries found.")
    txt_lines = parse_txt_labels(Path(args.lyrics_txt))
    labeled = map_labels(lrc_entries, txt_lines)
    audio_duration = get_audio_duration(Path(args.audio)) if args.audio else None
    payload = build_json(labeled, audio_duration)
    Path(args.output_json).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote JSON: {args.output_json}")


if __name__ == "__main__":
    main()
