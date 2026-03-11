#!/usr/bin/env python3
"""
jet_cut.py — ジェットカット処理

narration.wav の無音期間を librosa で検出し:
  1. 無音を短縮した narration_jetcut.wav を生成
  2. generated SUBTITLE_TIMELINE .ts のフレーム番号を更新
  3. ViralVideo TSX の SCENE_TIMELINE / INTERRUPT_FRAMES / SFX_EVENTS / totalFrames を更新
  4. TSX 内の Audio src を narration_jetcut.wav に差し替え

Usage:
  python jet_cut.py \\
    --audio  /path/to/narration.wav \\
    --tsx    /path/to/ViralVideo_xxx.tsx \\
    [--generated-ts  /path/to/subtitles.ts]   # 省略時は TSX import から自動検出
    [--min-silence   0.20]   # この秒数以上の無音を切る（デフォルト 0.20s）
    [--keep-silence  0.08]   # 切後に残す無音・食い気味（デフォルト 0.08s）
    [--top-db        40]     # 無音判定 dB 閾値（大きいほど厳しく・デフォルト 40）
    [--dry-run]              # ファイル変更せず結果だけ表示
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

try:
    import librosa
except ImportError:
    raise SystemExit(
        "librosa が見つかりません。"
        "setup/requirements.txt に含まれていますが、"
        "'python -m pip install librosa' でもインストールできます。"
    )

FPS = 30
DEFAULT_MIN_SILENCE_S = 0.20
DEFAULT_KEEP_SILENCE_S = 0.08
DEFAULT_TOP_DB = 40


# ──────────────────────────────────────────────────────────────
# 1. 無音検出 & タイムマップ構築
# ──────────────────────────────────────────────────────────────

def build_cut_plan(
    audio: np.ndarray,
    sr: int,
    min_silence_s: float,
    keep_silence_s: float,
    top_db: float,
) -> tuple[list[tuple[int, int]], list[tuple[float, float]]]:
    """
    Returns:
        chunks:  [(start_sample, end_sample), ...] 新しい audio を構成するスライス
        anchors: [(old_t, new_t), ...] 時刻リマップ用アンカー（単調増加）
    """
    intervals = librosa.effects.split(
        audio, top_db=top_db, frame_length=512, hop_length=128
    )
    # intervals: [[start_sample, end_sample], ...]

    if len(intervals) == 0:
        total_t = len(audio) / sr
        return [], [(0.0, 0.0), (total_t, total_t)]

    keep_samples = int(keep_silence_s * sr)
    chunks: list[tuple[int, int]] = []
    anchors: list[tuple[float, float]] = []
    cumulative_cut = 0.0

    # 先頭の無音
    pre_start = 0
    pre_end = int(intervals[0][0])
    pre_gap_s = pre_end / sr
    if pre_gap_s > min_silence_s:
        cut_s = pre_gap_s - keep_silence_s
        actual_keep = min(keep_samples, pre_end)
        chunks.append((0, actual_keep))
        anchors.append((0.0, 0.0))
        anchors.append((pre_gap_s, actual_keep / sr))
        cumulative_cut += cut_s
    elif pre_end > 0:
        chunks.append((0, pre_end))
        anchors.append((0.0, 0.0))
        anchors.append((pre_gap_s, pre_gap_s))

    # 各発話区間 + 後続 gap
    for i, (start, end) in enumerate(intervals):
        start_t = start / sr
        end_t = end / sr
        new_start_t = start_t - cumulative_cut
        new_end_t = end_t - cumulative_cut

        anchors.append((start_t, new_start_t))
        chunks.append((int(start), int(end)))
        anchors.append((end_t, new_end_t))

        if i + 1 < len(intervals):
            next_start = int(intervals[i + 1][0])
            gap_s = (next_start - end) / sr
            if gap_s > min_silence_s:
                cut_s = gap_s - keep_silence_s
                keep_end = end + min(keep_samples, next_start - end)
                chunks.append((int(end), keep_end))
                cumulative_cut += cut_s
            else:
                if int(end) < next_start:
                    chunks.append((int(end), next_start))

    # 末尾の無音
    last_end = int(intervals[-1][1])
    total_samples = len(audio)
    trailing_s = (total_samples - last_end) / sr
    if trailing_s > min_silence_s:
        cut_s = trailing_s - keep_silence_s
        trailing_keep = last_end + min(keep_samples, total_samples - last_end)
        chunks.append((last_end, trailing_keep))
        cumulative_cut += cut_s
    elif last_end < total_samples:
        chunks.append((last_end, total_samples))

    # 最終アンカー
    old_total = len(audio) / sr
    new_total = sum((e - s) for s, e in chunks) / sr
    anchors.append((old_total, new_total))

    # 重複を除去して単調増加に整理
    seen: set[float] = set()
    clean: list[tuple[float, float]] = []
    for a in sorted(anchors):
        if a[0] not in seen:
            seen.add(a[0])
            clean.append(a)

    return chunks, clean


def remap_time(t: float, anchors: list[tuple[float, float]]) -> float:
    """piecewise linear で old_t → new_t を変換する。"""
    if not anchors:
        return t
    if t <= anchors[0][0]:
        return anchors[0][1] + (t - anchors[0][0])
    if t >= anchors[-1][0]:
        return anchors[-1][1] + (t - anchors[-1][0])
    for i in range(len(anchors) - 1):
        a0, b0 = anchors[i]
        a1, b1 = anchors[i + 1]
        if a0 <= t <= a1:
            ratio = (t - a0) / (a1 - a0) if a1 > a0 else 0.0
            return b0 + ratio * (b1 - b0)
    return t


def remap_frame(frame: int, fps: int, anchors: list[tuple[float, float]]) -> int:
    return round(remap_time(frame / fps, anchors) * fps)


# ──────────────────────────────────────────────────────────────
# 2. generated SUBTITLE_TIMELINE .ts の更新
# ──────────────────────────────────────────────────────────────

def update_generated_ts(
    ts_path: Path,
    anchors: list[tuple[float, float]],
    fps: int,
    dry_run: bool = False,
) -> str:
    """{ from: N, to: M, text: ... } の N/M を remap して返す（元ファイルも更新）。"""
    text = ts_path.read_text(encoding="utf-8")
    original = text

    def replace_entry(m: re.Match) -> str:
        old_from = int(m.group(1))
        old_to   = int(m.group(2))
        new_from = remap_frame(old_from, fps, anchors)
        new_to   = remap_frame(old_to,   fps, anchors)
        return m.group(0).replace(
            f"from: {old_from},", f"from: {new_from},"
        ).replace(
            f"to: {old_to},", f"to: {new_to},"
        )

    text = re.sub(
        r"\{ from: (\d+), to: (\d+), text:",
        replace_entry,
        text,
    )

    if not dry_run and text != original:
        ts_path.write_text(text, encoding="utf-8")

    return text


# ──────────────────────────────────────────────────────────────
# 3. ViralVideo TSX の更新
# ──────────────────────────────────────────────────────────────

def update_tsx(
    tsx_path: Path,
    anchors: list[tuple[float, float]],
    fps: int,
    new_total_frames: int,
    old_audio_name: str,
    new_audio_name: str,
    dry_run: bool = False,
) -> str:
    text = tsx_path.read_text(encoding="utf-8")
    original = text

    # --- totalFrames ---
    text = re.sub(
        r"(const totalFrames\s*=\s*)\d+",
        f"\\g<1>{new_total_frames}",
        text,
    )

    # --- SCENE_TIMELINE: { from: N, to: M, src: ... } ---
    def remap_scene(m: re.Match) -> str:
        old_from = int(m.group(1))
        old_to   = int(m.group(2))
        new_from = remap_frame(old_from, fps, anchors)
        new_to   = remap_frame(old_to,   fps, anchors)
        result = m.group(0)
        result = re.sub(r"from:\s*\d+", f"from: {new_from}", result, count=1)
        result = re.sub(r"to:\s*\d+",   f"to: {new_to}",    result, count=1)
        return result

    text = re.sub(
        r"\{\s*from:\s*(\d+),\s*to:\s*(\d+),\s*src:",
        remap_scene,
        text,
    )

    # --- INTERRUPT_FRAMES: [N, M, ...] ---
    def remap_interrupt(m: re.Match) -> str:
        old_frames = list(map(int, re.findall(r"\d+", m.group(1))))
        new_frames = [remap_frame(f, fps, anchors) for f in old_frames]
        return m.group(0).replace(m.group(1), ", ".join(map(str, new_frames)))

    text = re.sub(
        r"const INTERRUPT_FRAMES[^=]*=\s*\[([^\]]+)\]",
        remap_interrupt,
        text,
    )

    # --- SFX_EVENTS: { from: N, ... } ---
    def remap_sfx_from(m: re.Match) -> str:
        old_from = int(m.group(1))
        new_from = remap_frame(old_from, fps, anchors)
        return m.group(0).replace(f"from: {old_from},", f"from: {new_from},")

    # SFX entries don't have "src:" immediately after "from:", they have "durationInFrames:"
    text = re.sub(
        r"\{\s*from:\s*(\d+),\s*durationInFrames:",
        remap_sfx_from,
        text,
    )

    # --- audio src: narration.wav → narration_jetcut.wav ---
    text = text.replace(old_audio_name, new_audio_name)

    if not dry_run and text != original:
        tsx_path.write_text(text, encoding="utf-8")

    return text


# ──────────────────────────────────────────────────────────────
# 4. main
# ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ジェットカット: narration.wav の無音を短縮して TSX タイムラインを更新する"
    )
    parser.add_argument("--audio", "-a", type=Path, required=True,
                        help="入力 narration.wav パス")
    parser.add_argument("--tsx", "-t", type=Path, required=True,
                        help="ViralVideo_xxx.tsx パス")
    parser.add_argument("--generated-ts", type=Path, default=None,
                        help="SUBTITLE_TIMELINE .ts パス（省略時は TSX の import から自動検出）")
    parser.add_argument("--min-silence", type=float, default=DEFAULT_MIN_SILENCE_S,
                        help=f"この秒数以上の無音を切る（デフォルト: {DEFAULT_MIN_SILENCE_S}）")
    parser.add_argument("--keep-silence", type=float, default=DEFAULT_KEEP_SILENCE_S,
                        help=f"切後に残す無音・食い気味（デフォルト: {DEFAULT_KEEP_SILENCE_S}）")
    parser.add_argument("--top-db", type=float, default=DEFAULT_TOP_DB,
                        help=f"無音判定 dB 閾値（デフォルト: {DEFAULT_TOP_DB}）")
    parser.add_argument("--dry-run", action="store_true",
                        help="ファイルを変更せず結果だけ表示する")
    args = parser.parse_args()

    if not args.audio.exists():
        print(f"ERROR: audio not found: {args.audio}", file=sys.stderr)
        return 1
    if not args.tsx.exists():
        print(f"ERROR: tsx not found: {args.tsx}", file=sys.stderr)
        return 1

    # generated-ts の自動検出
    generated_ts = args.generated_ts
    if generated_ts is None:
        tsx_text = args.tsx.read_text(encoding="utf-8")
        m = re.search(
            r'import\s*\{[^}]*SUBTITLE_TIMELINE[^}]*\}\s*from\s*["\']([^"\']+)["\']',
            tsx_text,
        )
        if m:
            rel = m.group(1)
            candidate = (args.tsx.parent / rel).resolve()
            if not candidate.suffix:
                candidate = candidate.with_suffix(".ts")
            if candidate.exists():
                generated_ts = candidate
                print(f"generated-ts 自動検出: {generated_ts}")
            else:
                print(f"WARNING: generated-ts が見つかりません: {candidate}")

    # ── 音声読み込み ──
    print(f"音声読み込み: {args.audio}")
    audio_data, sr = sf.read(str(args.audio), dtype="float32")
    if audio_data.ndim > 1:
        audio_mono = audio_data.mean(axis=1)
    else:
        audio_mono = audio_data

    original_duration = len(audio_mono) / sr
    print(f"  元の尺: {original_duration:.2f}s  ({round(original_duration * FPS)} frames)")

    # ── ジェットカット計画 ──
    chunks, anchors = build_cut_plan(
        audio_mono, sr,
        min_silence_s=args.min_silence,
        keep_silence_s=args.keep_silence,
        top_db=args.top_db,
    )

    new_audio_mono = np.concatenate(
        [audio_mono[s:e] for s, e in chunks]
    ) if chunks else np.zeros(0, dtype=np.float32)
    new_duration = len(new_audio_mono) / sr
    new_total_frames = round(new_duration * FPS)
    saved = original_duration - new_duration

    print(f"  カット後: {new_duration:.2f}s  ({new_total_frames} frames)  短縮: -{saved:.2f}s")

    # gap ごとの詳細表示
    intervals = librosa.effects.split(audio_mono, top_db=args.top_db,
                                       frame_length=512, hop_length=128)
    print(f"\n  検出した発話区間: {len(intervals)} 件")
    cut_count = 0
    for i in range(len(intervals) - 1):
        gap_s = (intervals[i + 1][0] - intervals[i][1]) / sr
        if gap_s > args.min_silence:
            kept = min(gap_s, args.keep_silence)
            print(f"    gap {i+1}: {gap_s:.3f}s → {kept:.3f}s (−{gap_s - kept:.3f}s)")
            cut_count += 1
    if cut_count == 0:
        print("  カット対象の無音なし。処理を終了します。")
        return 0

    if args.dry_run:
        print("\n[dry-run] ファイルは変更しません。")
        return 0

    # ── バックアップ & 出力 ──
    # audio: 同フォルダに narration_jetcut.wav
    out_audio = args.audio.parent / args.audio.name.replace(".wav", "_jetcut.wav")

    # ステレオ維持
    if audio_data.ndim > 1:
        # モノラル比率でステレオを同じカット比率で再構築
        new_audio_out = np.stack(
            [np.concatenate([audio_data[s:e, ch] for s, e in chunks])
             for ch in range(audio_data.shape[1])],
            axis=1,
        )
    else:
        new_audio_out = new_audio_mono

    sf.write(str(out_audio), new_audio_out, sr)
    print(f"\n音声出力: {out_audio}")

    # generated .ts
    if generated_ts and generated_ts.exists():
        backup_ts = generated_ts.with_suffix(".before_jetcut.ts")
        shutil.copy(generated_ts, backup_ts)
        update_generated_ts(generated_ts, anchors, FPS, dry_run=False)
        print(f"SUBTITLE_TIMELINE 更新: {generated_ts}  (backup: {backup_ts.name})")

    # TSX
    tsx_backup = args.tsx.with_suffix(".before_jetcut.tsx")
    shutil.copy(args.tsx, tsx_backup)
    update_tsx(
        args.tsx, anchors, FPS, new_total_frames,
        old_audio_name=args.audio.name,
        new_audio_name=out_audio.name,
        dry_run=False,
    )
    print(f"TSX 更新: {args.tsx}  (backup: {tsx_backup.name})")

    print("\n完了。プレビュー:")
    print(f"  npm --prefix /Users/deguchishouma/team-info/Remotion/my-video run dev")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
