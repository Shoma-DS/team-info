import argparse
import json
import os
import re
import sys
from faster_whisper import WhisperModel
from tqdm import tqdm
import subprocess

TOKEN_RE = re.compile(r"[A-Za-z0-9'’]+|[一-龥々〆〤ぁ-んァ-ヶー]+|[^\s]")


def get_audio_duration(file_path):
    """Get audio duration in seconds using ffprobe."""
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not determine audio duration for progress bar: {e}")
        return None


def format_lrc_timestamp(seconds):
    """Format seconds to [mm:ss.xx] for LRC."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"[{m:02d}:{s:02d}.{cs:02d}]"


def format_srt_timestamp(seconds):
    """Format seconds to HH:MM:SS,mmm for SRT."""
    total_ms = int(max(0.0, seconds) * 1000)
    h = total_ms // 3_600_000
    rem = total_ms % 3_600_000
    m = rem // 60_000
    rem = rem % 60_000
    s = rem // 1000
    ms = rem % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def tokenize(text):
    return TOKEN_RE.findall(text)


def visible_len(text):
    return len(re.sub(r"[\s\u3000]", "", text))


def build_karaoke_json(entries):
    payload = []
    for entry in entries:
        start = float(entry["start"])
        end = float(entry["end"])
        text = entry["text"]
        duration = max(0.20, end - start)

        words = tokenize(text)
        if not words:
            words = [text]
        weights = [max(1, visible_len(w)) for w in words]
        total = sum(weights)
        cursor = 0.0
        word_items = []
        for w, wt in zip(words, weights):
            wdur = duration * (wt / total)
            wstart = round(cursor, 2)
            wend = round(min(duration, cursor + wdur), 2)
            word_items.append({"word": w, "start": wstart, "end": wend})
            cursor += wdur

        payload.append(
            {
                "time": round(start, 2),
                "duration": round(duration, 2),
                "text": text,
                "label": "Verse",
                "emotion": "",
                "words": word_items,
                "animation": {"in": "Karaoke", "out": "FadeOut", "props": {"inDurationFrames": 10, "outDurationFrames": 8}},
            }
        )
    return payload


def get_line_start_from_words(segment):
    """
    Use the first non-empty word timestamp when available.
    This gives tighter "first character" alignment than raw segment.start.
    """
    words = getattr(segment, "words", None) or []
    for word in words:
        token = (getattr(word, "word", "") or "").strip()
        start = getattr(word, "start", None)
        if token and start is not None:
            return max(0.0, float(start))
    return max(0.0, float(segment.start))


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio to LRC/SRT using faster-whisper.")
    parser.add_argument("audio_path", help="Path to the input audio file")
    parser.add_argument("--lyrics", help="Path to text file containing lyrics (for prompting/context)", default=None)
    parser.add_argument("--output", help="Path to output subtitle file", default=None)
    parser.add_argument("--json", help="Optional output path for lyric_animation_data.json", default=None)
    parser.add_argument(
        "--output-format",
        "--output_format",
        "--format",
        dest="output_format",
        choices=["lrc", "srt"],
        default=None,
        help="Subtitle output format (lrc or srt). If omitted, infer from --output extension, else lrc.",
    )
    parser.add_argument("--model", help="Whisper model size", default="medium")
    parser.add_argument("--language", help="Language code", default="ja")
    parser.add_argument("--device", help="Device to use (cuda or cpu)", default="cpu")
    parser.add_argument("--intro-label", help="Intro caption text for the gap before first lyric", default="(イントロ)")
    parser.add_argument(
        "--intro-min-seconds",
        type=float,
        default=0.30,
        help="Insert intro line when first lyric starts at or after this second value",
    )
    parser.add_argument("--always-intro", action="store_true", help="Always insert intro at 00:00.00")
    parser.add_argument("--disable-intro", action="store_true", help="Never insert intro line")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar output")

    args = parser.parse_args()

    if not os.path.exists(args.audio_path):
        print(f"Error: Audio file not found: {args.audio_path}")
        sys.exit(1)

    # Determine output format
    output_format = args.output_format
    if output_format is None and args.output:
        ext = os.path.splitext(args.output)[1].lower()
        if ext in [".lrc", ".srt"]:
            output_format = ext[1:]
    if output_format is None:
        output_format = "lrc"

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.splitext(args.audio_path)[0] + f".{output_format}"
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    if args.json:
        json_dir = os.path.dirname(args.json)
        if json_dir:
            os.makedirs(json_dir, exist_ok=True)

    # Prepare initial prompt from lyrics file if provided
    initial_prompt = None
    if args.lyrics and os.path.exists(args.lyrics):
        with open(args.lyrics, "r", encoding="utf-8") as f:
            initial_prompt = f.read()
        print(f"Loaded lyrics for context prompt from: {args.lyrics}")

    print(f"[1/3] Loading Whisper model ({args.model})...")
    try:
        model = WhisperModel(args.model, device=args.device, compute_type="int8")
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

    duration = get_audio_duration(args.audio_path)
    
    print(f"[2/3] Starting transcription for: {args.audio_path}")
    print(f"       Output will be saved to: {output_path}")

    segments, _ = model.transcribe(args.audio_path, language=args.language, initial_prompt=initial_prompt, word_timestamps=True)

    # Prepare progress bar
    pbar = None
    progress_by_seconds = duration is not None
    if not args.no_progress:
        if progress_by_seconds:
            pbar = tqdm(
                total=duration,
                unit="sec",
                desc="Transcribing",
                bar_format="{l_bar}{bar}| {n:.1f}/{total:.1f}s [{elapsed}<{remaining}]",
            )
        else:
            pbar = tqdm(total=0, unit="seg", desc="Transcribing", bar_format="{l_bar}{n} segments [{elapsed}]")

    timed_lines = []
    current_time = 0.0
    for segment in segments:
        end_time = max(0.0, float(segment.end))
        if pbar:
            if progress_by_seconds:
                pbar.update(max(0.0, end_time - current_time))
            else:
                pbar.update(1)
            current_time = end_time
        text = (segment.text or "").strip()
        if not text:
            continue
        start_time = get_line_start_from_words(segment)
        if end_time <= start_time:
            end_time = start_time + 0.20
        timed_lines.append({"start": start_time, "end": end_time, "text": text})

    if pbar:
        pbar.close()

    first_lyric_start = timed_lines[0]["start"] if timed_lines else None
    should_insert_intro = False
    if not args.disable_intro and args.intro_label:
        if not timed_lines:
            should_insert_intro = True
        elif args.always_intro:
            should_insert_intro = True
        elif first_lyric_start is not None and first_lyric_start >= max(0.0, args.intro_min_seconds):
            should_insert_intro = True

    lrc_lines = []
    srt_entries = []
    if should_insert_intro:
        first_text = timed_lines[0]["text"] if timed_lines else ""
        if first_text != args.intro_label:
            lrc_lines.append(f"{format_lrc_timestamp(0.0)}{args.intro_label}")
            print(f"Inserted intro line at 00:00.00: {args.intro_label}")
            intro_end = 2.00
            if first_lyric_start is not None:
                intro_end = max(0.20, first_lyric_start - 0.01)
            srt_entries.append({"start": 0.0, "end": intro_end, "text": args.intro_label})

    for i, line in enumerate(timed_lines):
        start_time = line["start"]
        end_time = line["end"]
        if i + 1 < len(timed_lines):
            next_start = timed_lines[i + 1]["start"]
            end_time = min(end_time, max(start_time + 0.20, next_start - 0.01))
        lrc_lines.append(f"{format_lrc_timestamp(start_time)}{line['text']}")
        srt_entries.append({"start": start_time, "end": max(end_time, start_time + 0.20), "text": line["text"]})

    if first_lyric_start is not None:
        print(f"First lyric start detected at: {format_lrc_timestamp(first_lyric_start)} ({first_lyric_start:.2f}s)")

    print("[3/3] Writing subtitle file...")

    if output_format == "lrc":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lrc_lines))
        print(f"\nSuccess! LRC file created at: {output_path}")
    else:
        # output_format == "srt"
        srt_lines = []
        for idx, entry in enumerate(srt_entries, start=1):
            srt_lines.append(str(idx))
            srt_lines.append(f"{format_srt_timestamp(entry['start'])} --> {format_srt_timestamp(entry['end'])}")
            srt_lines.append(entry["text"])
            srt_lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines).rstrip() + "\n")

        print(f"\nSuccess! SRT file created at: {output_path}")

    if args.json:
        json_payload = build_karaoke_json(srt_entries)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Success! JSON file created at: {args.json}")

if __name__ == "__main__":
    main()
