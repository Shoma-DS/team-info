#!/usr/bin/env python3
"""
sync_subtitles_to_audio: セクション別 WAV の無音区間を解析し、
subtitles.json の各セクション開始を実際の発話開始に合わせて補正する。

主な用途:
  - VOICEVOX 音声の先頭無音ぶん、字幕が早く出るズレを補正する
  - セクションごとの実発話尺に合わせて字幕セグメントを再配分する
  - 必要なら Remotion 用の SUBTITLE_TIMELINE TS モジュールも出力する
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import wave
from array import array
from dataclasses import asdict, dataclass
from pathlib import Path


SECTION_AUDIO_FILES = {
    "hook": "00_hook.wav",
    "opening": "01_opening.wav",
    "s1": "02_s1.wav",
    "s2": "03_s2.wav",
    "s3": "04_s3.wav",
    "cta": "05_cta.wav",
}


@dataclass
class SpeechWindow:
    section: str
    audio_file: str
    clip_start: float
    clip_end: float
    speech_start: float
    speech_end: float
    duration: float
    leading_silence: float
    trailing_silence: float
    peak_rms: float
    threshold_rms: float


def _load_pcm_samples(wav_path: Path) -> tuple[array, int, int]:
    with wave.open(str(wav_path), "rb") as wav_file:
        sample_width = wav_file.getsampwidth()
        channels = wav_file.getnchannels()
        frame_rate = wav_file.getframerate()
        pcm = wav_file.readframes(wav_file.getnframes())

    if sample_width != 2:
        raise SystemExit(
            f"未対応のサンプル幅です: {wav_path} ({sample_width} bytes)\n"
            "現在は 16-bit PCM WAV のみ対応しています。"
        )

    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()

    return samples, channels, frame_rate


def _compute_chunk_rms(
    samples: array,
    channels: int,
    chunk_frames: int,
) -> list[float]:
    total_frames = len(samples) // channels
    values: list[float] = []

    for frame_start in range(0, total_frames, chunk_frames):
        frame_end = min(total_frames, frame_start + chunk_frames)
        sample_start = frame_start * channels
        sample_end = frame_end * channels

        sum_sq = 0.0
        sample_count = 0
        for sample in samples[sample_start:sample_end]:
            value = float(sample)
            sum_sq += value * value
            sample_count += 1

        rms = math.sqrt(sum_sq / sample_count) if sample_count else 0.0
        values.append(rms)

    return values


def _find_first_run(values: list[float], threshold: float, min_run: int) -> int | None:
    run_length = 0
    for index, value in enumerate(values):
        run_length = run_length + 1 if value >= threshold else 0
        if run_length >= min_run:
            return index - min_run + 1
    return None


def _find_last_run(values: list[float], threshold: float, min_run: int) -> int | None:
    run_length = 0
    for reverse_index, value in enumerate(reversed(values)):
        index = len(values) - 1 - reverse_index
        run_length = run_length + 1 if value >= threshold else 0
        if run_length >= min_run:
            return index + min_run
    return None


def analyze_speech_window(
    wav_path: Path,
    *,
    chunk_ms: int = 10,
    threshold_ratio: float = 0.08,
    min_threshold: float = 250.0,
    min_run_chunks: int = 3,
) -> tuple[float, float, float, float, float]:
    samples, channels, frame_rate = _load_pcm_samples(wav_path)
    chunk_frames = max(1, int(frame_rate * (chunk_ms / 1000)))
    total_frames = len(samples) // channels
    duration = total_frames / frame_rate

    rms_values = _compute_chunk_rms(samples, channels, chunk_frames)
    peak_rms = max(rms_values, default=0.0)
    threshold_rms = max(min_threshold, peak_rms * threshold_ratio)

    onset_chunk = _find_first_run(rms_values, threshold_rms, min_run_chunks)
    offset_chunk = _find_last_run(rms_values, threshold_rms, min_run_chunks)

    if onset_chunk is None or offset_chunk is None:
        return 0.0, duration, duration, peak_rms, threshold_rms

    onset = onset_chunk * chunk_frames / frame_rate
    offset = min(duration, offset_chunk * chunk_frames / frame_rate)
    if offset <= onset:
        offset = duration

    return onset, offset, duration, peak_rms, threshold_rms


def analyze_section_audio(
    audio_dir: Path,
    section_order: list[str],
    *,
    chunk_ms: int = 10,
    threshold_ratio: float = 0.08,
    min_threshold: float = 250.0,
    min_run_chunks: int = 3,
) -> dict[str, SpeechWindow]:
    windows: dict[str, SpeechWindow] = {}
    clip_start = 0.0

    for section in section_order:
        audio_name = SECTION_AUDIO_FILES.get(section)
        if not audio_name:
            raise SystemExit(f"未対応のセクションです: {section}")

        wav_path = audio_dir / audio_name
        if not wav_path.exists():
            raise SystemExit(f"音源が見つかりません: {wav_path}")

        lead, speech_end_in_clip, duration, peak_rms, threshold_rms = analyze_speech_window(
            wav_path,
            chunk_ms=chunk_ms,
            threshold_ratio=threshold_ratio,
            min_threshold=min_threshold,
            min_run_chunks=min_run_chunks,
        )
        clip_end = clip_start + duration
        trailing_silence = max(0.0, duration - speech_end_in_clip)

        windows[section] = SpeechWindow(
            section=section,
            audio_file=audio_name,
            clip_start=clip_start,
            clip_end=clip_end,
            speech_start=clip_start + lead,
            speech_end=clip_start + speech_end_in_clip,
            duration=duration,
            leading_silence=lead,
            trailing_silence=trailing_silence,
            peak_rms=peak_rms,
            threshold_rms=threshold_rms,
        )
        clip_start = clip_end

    return windows


def _section_order_from_segments(segments: list[dict]) -> list[str]:
    seen: set[str] = set()
    order: list[str] = []
    for segment in segments:
        section = str(segment["section"])
        if section not in seen:
            seen.add(section)
            order.append(section)
    return order


def _round_time(seconds: float) -> float:
    return round(seconds + 1e-9, 3)


def sync_subtitles_data(
    data: dict,
    windows: dict[str, SpeechWindow],
) -> tuple[dict, list[SpeechWindow]]:
    fps = int(data["fps"])
    total_frames = int(data.get("total_frames", 0))
    segments = [dict(segment) for segment in data["segments"]]
    section_order = _section_order_from_segments(segments)

    by_section: dict[str, list[dict]] = {}
    for segment in segments:
        by_section.setdefault(str(segment["section"]), []).append(segment)

    global_prev_to_frame = 0
    for section in section_order:
        section_segments = by_section[section]
        window = windows[section]

        original_start = float(section_segments[0]["from_time"])
        original_end = float(section_segments[-1]["to_time"])
        original_duration = max(0.001, original_end - original_start)
        speech_duration = max(0.001, window.speech_end - window.speech_start)

        for segment in section_segments:
            relative_from = (float(segment["from_time"]) - original_start) / original_duration
            relative_to = (float(segment["to_time"]) - original_start) / original_duration
            synced_from = window.speech_start + (relative_from * speech_duration)
            synced_to = window.speech_start + (relative_to * speech_duration)

            from_frame = max(global_prev_to_frame, round(synced_from * fps))
            to_frame = round(synced_to * fps)
            if total_frames:
                from_frame = min(from_frame, max(0, total_frames - 1))
                to_frame = min(to_frame, total_frames)
            if to_frame <= from_frame:
                to_frame = from_frame + 1
                if total_frames:
                    to_frame = min(to_frame, total_frames)
                    from_frame = max(0, min(from_frame, to_frame - 1))

            segment["from_frame"] = from_frame
            segment["to_frame"] = to_frame
            segment["from_time"] = _round_time(from_frame / fps)
            segment["to_time"] = _round_time(to_frame / fps)
            global_prev_to_frame = to_frame

    updated = dict(data)
    updated["segments"] = segments
    updated["audio_sync"] = {
        "synced_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "narration_duration_seconds": _round_time(
            max((window.clip_end for window in windows.values()), default=0.0)
        ),
        "sections": [asdict(windows[section]) for section in section_order],
    }
    return updated, [windows[section] for section in section_order]


def write_timeline_ts_module(timeline_ts_path: Path, segments: list[dict]) -> None:
    lines = [
        "/** Auto-generated by sync_subtitles_to_audio.py. */",
        "export const SUBTITLE_TIMELINE: { from: number; to: number; text: string }[] = [",
    ]
    for segment in segments:
        text = json.dumps(segment["text"], ensure_ascii=False)
        lines.append(
            f"  {{ from: {segment['from_frame']}, to: {segment['to_frame']}, text: {text} }},"
        )
    lines.append("];")
    lines.append("")

    timeline_ts_path.parent.mkdir(parents=True, exist_ok=True)
    timeline_ts_path.write_text("\n".join(lines), encoding="utf-8")


def sync_subtitles_file(
    subtitles_path: Path,
    audio_dir: Path,
    *,
    output_path: Path | None = None,
    timeline_ts_path: Path | None = None,
    chunk_ms: int = 10,
    threshold_ratio: float = 0.08,
    min_threshold: float = 250.0,
    min_run_chunks: int = 3,
) -> tuple[dict, list[SpeechWindow]]:
    data = json.loads(subtitles_path.read_text(encoding="utf-8"))
    section_order = _section_order_from_segments(data["segments"])
    windows = analyze_section_audio(
        audio_dir,
        section_order,
        chunk_ms=chunk_ms,
        threshold_ratio=threshold_ratio,
        min_threshold=min_threshold,
        min_run_chunks=min_run_chunks,
    )
    synced, ordered_windows = sync_subtitles_data(data, windows)

    destination = output_path or subtitles_path
    destination.write_text(
        json.dumps(synced, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if timeline_ts_path:
        write_timeline_ts_module(timeline_ts_path, synced["segments"])

    return synced, ordered_windows


def main() -> None:
    parser = argparse.ArgumentParser(description="音源に合わせて subtitles.json を補正")
    parser.add_argument("--subtitles", type=Path, required=True, help="subtitles.json の絶対パス")
    parser.add_argument("--audio-dir", type=Path, required=True, help="セクション WAV がある audio ディレクトリ")
    parser.add_argument("--output", type=Path, default=None, help="出力先。省略時は上書き")
    parser.add_argument("--timeline-ts", type=Path, default=None, help="Remotion 用 TS モジュール出力先")
    parser.add_argument("--chunk-ms", type=int, default=10, help="RMS 解析のチャンク幅 (default: 10)")
    parser.add_argument("--threshold-ratio", type=float, default=0.08, help="ピーク RMS に対する発話判定比率")
    parser.add_argument("--min-threshold", type=float, default=250.0, help="発話判定の最小 RMS")
    parser.add_argument("--min-run-chunks", type=int, default=3, help="連続発話とみなす最小チャンク数")
    args = parser.parse_args()

    synced, windows = sync_subtitles_file(
        subtitles_path=args.subtitles,
        audio_dir=args.audio_dir,
        output_path=args.output,
        timeline_ts_path=args.timeline_ts,
        chunk_ms=args.chunk_ms,
        threshold_ratio=args.threshold_ratio,
        min_threshold=args.min_threshold,
        min_run_chunks=args.min_run_chunks,
    )

    print(f"更新: {args.output or args.subtitles}")
    if args.timeline_ts:
        print(f"TS モジュール: {args.timeline_ts}")

    for window in windows:
        print(
            f"[{window.section}] "
            f"speech {window.speech_start:.3f}s -> {window.speech_end:.3f}s "
            f"(lead {window.leading_silence:.3f}s / trail {window.trailing_silence:.3f}s)"
        )

    first = synced["segments"][0]
    last = synced["segments"][-1]
    print(
        "字幕範囲: "
        f"{first['from_time']:.3f}s -> {last['to_time']:.3f}s "
        f"({first['from_frame']}f -> {last['to_frame']}f)"
    )


if __name__ == "__main__":
    main()
