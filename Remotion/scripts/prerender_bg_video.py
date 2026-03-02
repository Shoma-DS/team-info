#!/usr/bin/env python3
"""
prerender_bg_video.py
  背景動画を事前に1本に合成し、Remotionで単純読み込みできるファイルを生成する。
  クロスディゾルブをffmpegで処理済みにすることで、Remotionレンダリング時の負荷を排除する。

Usage (team-info/ から実行):
  python3 Remotion/scripts/prerender_bg_video.py \\
    --output Remotion/my-video/public/assets/songs/[曲名]/bg_prerendered.mp4 \\
    --segment-sec 5 \\
    --crossfade-sec 1 \\
    --total-sec 321 \\
    --fps 30 --width 1920 --height 1080 --seed 42 \\
    Remotion/my-video/public/assets/songs/[曲名]/*.mp4
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

# ffmpegの入力数を抑えるためのチャンクサイズ（セグメント数）
CHUNK_SIZE = 15
BAR_WIDTH = 40
SEP = "─" * 62


# ─── 表示ユーティリティ ──────────────────────────────────────

def parse_time_str(s: str) -> float | None:
    """'HH:MM:SS.xxxxxx' を秒数に変換する（ffmpeg -progress 出力用）。"""
    s = s.strip()
    try:
        parts = s.split(":")
        if len(parts) != 3:
            return None
        h, m, sec = int(parts[0]), int(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + sec
    except (ValueError, IndexError):
        return None


def format_duration(seconds: float) -> str:
    """秒数を読みやすい時間文字列に変換する。"""
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}時間{m}分{s:02d}秒"
    if m > 0:
        return f"{m}分{s:02d}秒"
    return f"{s}秒"


def print_progress(label: str, current: float, total: float, elapsed: float) -> None:
    """進捗バーを1行で上書き表示する（\\r 使用）。"""
    ratio = min(1.0, current / total) if total > 0 else 0.0
    filled = int(BAR_WIDTH * ratio)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    pct = ratio * 100

    eta_str = ""
    if elapsed > 1.0 and 0.02 < ratio < 1.0:
        eta_sec = int(elapsed / ratio - elapsed)
        m, s = divmod(eta_sec, 60)
        eta_str = f"  ETA {m:02d}:{s:02d}"

    line = f"\r  {label}  [{bar}] {pct:5.1f}%  {current:.1f}s / {total:.1f}s{eta_str}   "
    sys.stdout.write(line)
    sys.stdout.flush()


# ─── ffmpeg 実行（進捗バー付き）─────────────────────────────

def run_ffmpeg_with_progress(cmd: list[str], label: str, expected_sec: float) -> None:
    """
    ffmpeg を実行し、-progress pipe:1 出力を解析してリアルタイム進捗バーを表示する。
    エラーは stderr を通じてそのままターミナルに表示される。
    """
    # 出力ファイル（最終引数）の直前に -progress / -loglevel を挿入する
    out_file = cmd[-1]
    cmd_p = cmd[:-1] + ["-progress", "pipe:1", "-loglevel", "error", out_file]

    proc = subprocess.Popen(
        cmd_p,
        stdout=subprocess.PIPE,   # -progress pipe:1 の出力を受け取る
        stderr=None,              # エラーはそのままターミナルへ
        text=True,
        bufsize=1,
    )

    start = time.monotonic()

    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.strip()
        if line.startswith("out_time="):
            t = parse_time_str(line[len("out_time="):])
            if t is not None and t >= 0:
                elapsed = time.monotonic() - start
                print_progress(label, t, expected_sec, elapsed)

    proc.wait()
    elapsed = time.monotonic() - start

    # 完了時に100%表示して改行
    print_progress(label, expected_sec, expected_sec, elapsed)
    sys.stdout.write(f"  ({format_duration(elapsed)})\n")
    sys.stdout.flush()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg が失敗しました (終了コード: {proc.returncode})")


# ─── シャッフル順生成 ────────────────────────────────────────

def generate_sequence(n: int, total_segments: int, seed: int) -> list[int]:
    """ラウンド制Fisher-Yatesシャッフル。ラウンド境界で連続重複を防ぐ。"""
    rng = random.Random(seed)
    result: list[int] = []
    last_idx = -1
    while len(result) < total_segments:
        arr = list(range(n))
        for i in range(len(arr) - 1, 0, -1):
            j = rng.randint(0, i)
            arr[i], arr[j] = arr[j], arr[i]
        if n >= 2 and arr[0] == last_idx:
            swap_idx = rng.randint(1, n - 1)
            arr[0], arr[swap_idx] = arr[swap_idx], arr[0]
        result.extend(arr)
        last_idx = arr[-1]
    return result[:total_segments]


# ─── ffmpeg コマンド構築 ─────────────────────────────────────

def build_chunk_cmd(
    chunk_paths: list[str],
    output_path: str,
    segment_sec: float,
    crossfade_sec: float,
    fps: int,
    width: int,
    height: int,
    brightness: float,
    saturation: float,
) -> tuple[list[str], float]:
    """チャンクレンダリング用 ffmpeg コマンドと期待出力秒数を返す。"""
    n = len(chunk_paths)
    net_step = segment_sec - crossfade_sec
    expected_sec = n * segment_sec - (n - 1) * crossfade_sec

    cmd = ["ffmpeg", "-y"]
    for path in chunk_paths:
        cmd += ["-t", str(segment_sec), "-i", path]

    filters = []
    for i in range(n):
        filters.append(
            f"[{i}:v]"
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"setsar=1,"
            f"fps={fps},"
            f"colorchannelmixer=rr={brightness}:gg={brightness}:bb={brightness},"
            f"hue=s={saturation},"
            f"setpts=PTS-STARTPTS"
            f"[nv{i}]"
        )

    if n == 1:
        filters.append("[nv0]setpts=PTS-STARTPTS[out]")
    else:
        prev = "nv0"
        for i in range(1, n):
            offset = round(i * net_step, 6)
            out = f"xf{i}" if i < n - 1 else "out"
            filters.append(
                f"[{prev}][nv{i}]xfade=transition=fade:duration={crossfade_sec}:offset={offset}[{out}]"
            )
            prev = out

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[out]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an",
        output_path,
    ]

    return cmd, expected_sec


def get_video_duration(video_path: str) -> float:
    """ffprobe で動画の長さ（秒）を取得する。"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {video_path}")
    return float(json.loads(result.stdout)["format"]["duration"])


def build_join_cmd(
    chunk_files: list[str],
    output_path: str,
    crossfade_sec: float,
    total_sec: float,
    durations: list[float],
) -> list[str]:
    """チャンク結合用 ffmpeg コマンドを返す。"""
    n = len(chunk_files)
    cmd = ["ffmpeg", "-y"]
    for cf in chunk_files:
        cmd += ["-i", cf]

    filters = []
    for i in range(n):
        filters.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")

    prev = "v0"
    cumulative = 0.0
    for i in range(1, n):
        cumulative += durations[i - 1] - crossfade_sec
        out = f"xc{i}" if i < n - 1 else "preout"
        filters.append(
            f"[{prev}][v{i}]xfade=transition=fade:duration={crossfade_sec}:offset={round(cumulative, 6)}[{out}]"
        )
        prev = out

    # 目標尺にトリム
    filters.append(f"[{prev}]trim=duration={total_sec},setpts=PTS-STARTPTS[out]")

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[out]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an",
        output_path,
    ]

    return cmd


# ─── エントリポイント ────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="背景動画をシャッフル+クロスディゾルブで事前合成する"
    )
    parser.add_argument("--output", required=True, help="出力先 mp4 パス")
    parser.add_argument("--segment-sec", type=float, default=5.0, help="1セグメントの秒数")
    parser.add_argument("--crossfade-sec", type=float, default=1.0, help="クロスディゾルブの秒数")
    parser.add_argument("--total-sec", type=float, required=True, help="最終動画の長さ（秒）")
    parser.add_argument("--fps", type=int, default=30, help="出力フレームレート")
    parser.add_argument("--width", type=int, default=1920, help="出力幅")
    parser.add_argument("--height", type=int, default=1080, help="出力高さ")
    parser.add_argument("--seed", type=int, default=42, help="シャッフル用シード")
    parser.add_argument("--brightness", type=float, default=0.68, help="輝度係数（CSS brightness相当）")
    parser.add_argument("--saturation", type=float, default=0.72, help="彩度係数（CSS saturate相当）")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="チャンクあたりのセグメント数")
    parser.add_argument("videos", nargs="+", help="入力動画ファイル（複数可）")
    args = parser.parse_args()

    n_videos = len(args.videos)
    net_step = args.segment_sec - args.crossfade_sec
    if net_step <= 0:
        print("ERROR: --segment-sec > --crossfade-sec が必要です", file=sys.stderr)
        sys.exit(1)

    total_segments = int(args.total_sec / net_step) + 2
    chunk_count = (total_segments + args.chunk_size - 1) // args.chunk_size

    print(SEP)
    print("  背景動画プリレンダラー")
    print(SEP)
    print(f"  入力動画  : {n_videos} 本")
    print(f"  セグメント: {total_segments} 個 (各 {args.segment_sec}s、net {net_step}s/seg)")
    print(f"  目標尺    : {args.total_sec}s")
    print(f"  出力      : {args.output}")
    print(f"  解像度    : {args.width}×{args.height} @ {args.fps}fps")
    print(f"  輝度={args.brightness}  彩度={args.saturation}  seed={args.seed}")
    print(SEP)

    picked = generate_sequence(n_videos, total_segments, args.seed)
    picked_paths = [args.videos[i] for i in picked]

    overall_start = time.monotonic()
    tmpdir = tempfile.mkdtemp(prefix="bg_prerender_")
    chunk_files: list[str] = []

    try:
        # ── Phase 1: チャンクレンダリング ─────────────────────────
        print(f"\n  Phase 1/2  チャンクレンダリング  ({chunk_count} チャンク)")
        print(SEP)

        for ci, chunk_start in enumerate(range(0, total_segments, args.chunk_size)):
            chunk_end = min(chunk_start + args.chunk_size, total_segments)
            chunk_paths = picked_paths[chunk_start:chunk_end]
            chunk_file = os.path.join(tmpdir, f"chunk_{ci:04d}.mp4")
            chunk_files.append(chunk_file)

            n_in_chunk = len(chunk_paths)
            expected = n_in_chunk * args.segment_sec - (n_in_chunk - 1) * args.crossfade_sec

            print(f"\n  [{ci + 1}/{chunk_count}] セグメント {chunk_start}–{chunk_end - 1}"
                  f"  ({n_in_chunk} 本入力, 期待 {expected:.1f}s)")
            cmd, _ = build_chunk_cmd(
                chunk_paths, chunk_file,
                args.segment_sec, args.crossfade_sec,
                args.fps, args.width, args.height,
                args.brightness, args.saturation,
            )
            run_ffmpeg_with_progress(cmd, f"チャンク {ci + 1}/{chunk_count}", expected)

        # ── Phase 2: チャンク結合 ─────────────────────────────────
        print(f"\n  Phase 2/2  チャンク結合  ({len(chunk_files)} 本 → 1 本)")
        print(SEP)

        if len(chunk_files) == 1:
            cmd_copy = [
                "ffmpeg", "-y", "-i", chunk_files[0],
                "-t", str(args.total_sec),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-an",
                args.output,
            ]
            print(f"\n  チャンクが 1 本のため単純 trim コピー")
            run_ffmpeg_with_progress(cmd_copy, "コピー", args.total_sec)
        else:
            print(f"\n  チャンク長を計測中 ...")
            durations = [get_video_duration(f) for f in chunk_files]
            for i, d in enumerate(durations):
                print(f"    chunk[{i}]: {d:.2f}s")
            print()
            cmd_join = build_join_cmd(
                chunk_files, args.output, args.crossfade_sec, args.total_sec, durations
            )
            run_ffmpeg_with_progress(cmd_join, "結合", args.total_sec)

        # ── 完了 ──────────────────────────────────────────────────
        overall_elapsed = time.monotonic() - overall_start
        final_dur = get_video_duration(args.output)

        print(f"\n{SEP}")
        print(f"  完了  {args.output}")
        print(f"  最終動画: {final_dur:.3f}s  (目標: {args.total_sec}s)")
        print(f"  総処理時間: {format_duration(overall_elapsed)}")
        print(SEP)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
