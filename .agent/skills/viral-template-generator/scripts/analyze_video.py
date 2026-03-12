#!/usr/bin/env python3
"""
analyze-video: ショート動画3層解析 → analysis.json 生成

起動フロー:
  1. 新しく分析する  → パターン名_日付フォルダ(例: 芸能人エンタメ_20260312)を作成して全動画を一括解析
  2. 既存を使う      → 既存の分析バッチ一覧から選択してそのまま使う
  3. 上書き再解析    → 既存の分析バッチ一覧から選択して全動画を再解析

出力構造:
  inputs/viral-analysis/output/
  └── パターン名_YYYYMMDD/
      ├── {動画名}/
      │   ├── analysis.json
      │   ├── subtitle_style_template.json
      │   └── subtitle_style_samples/
      ├── viral_patterns.md     ← Phase A 以降（Claude が生成）
      └── ...

Usage:
  # 対話モード（推奨）
  python3 analyze_video.py

  # 直接指定（非対話 / CI 用）
  python3 analyze_video.py /path/to/video.mp4 --platform shorts --pattern-name 芸能人エンタメ --date 20260311
  python3 analyze_video.py --all --platform shorts --pattern-name 芸能人エンタメ --date 20260311
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_config_dir, get_repo_root

# ─── パス定数 ─────────────────────────────────────────────────────────────────
PROJECT_ROOT = get_repo_root()

# 動画置き場（ここに .mp4 を置く）
INBOX_DIR = PROJECT_ROOT / "inputs" / "viral-analysis"

# 解析結果の出力ベース
OUTPUT_BASE = PROJECT_ROOT / "inputs" / "viral-analysis" / "output"

# セットアップ完了フラグ
_SETUP_FLAG = get_config_dir("viral-template-generator") / ".setup_done"

# 対応動画拡張子
_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# 新旧どちらの分析バッチフォルダ名も受け入れる:
#   - 20260312
#   - 20260312_2
#   - 芸能人エンタメ_20260312
#   - 芸能人エンタメ_20260312_2
_BATCH_DIR_RE = re.compile(
    r"^(?:(?P<pattern>.+)_)?(?P<date>\d{8})(?:_(?P<suffix>\d+))?$"
)


# ─── クロスプラットフォーム通知 ──────────────────────────────────────────────

def _notify(title: str, message: str, sound: str = "Ping") -> None:
    if sys.platform == "darwin":
        script = (
            f'display notification "{message}" '
            f'with title "{title}" '
            f'sound name "{sound}"'
        )
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, check=False)
        except OSError:
            print("\a", end="", flush=True)

    elif sys.platform.startswith("linux"):
        try:
            subprocess.run(
                ["notify-send", "--app-name", title, title, message],
                capture_output=True, check=False,
            )
        except OSError:
            pass
        print("\a", end="", flush=True)

    elif sys.platform == "win32":
        ps_lines = [
            "Add-Type -AssemblyName System.Windows.Forms",
            "$n = New-Object System.Windows.Forms.NotifyIcon",
            "$n.Icon = [System.Drawing.SystemIcons]::Information",
            "$n.Visible = $true",
            f"$n.ShowBalloonTip(5000, '{title}', '{message}', [System.Windows.Forms.ToolTipIcon]::Info)",
            "[console]::beep(1000, 300)",
            "Start-Sleep -Milliseconds 5100",
            "$n.Dispose()",
        ]
        try:
            subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-Command", "\n".join(ps_lines)],
                capture_output=True, check=False,
            )
        except OSError:
            print("\a", end="", flush=True)
    else:
        print("\a", end="", flush=True)


# ─── セットアップ自動実行 ─────────────────────────────────────────────────────

def _ensure_setup() -> None:
    if os.environ.get("TEAM_INFO_IN_DOCKER") == "1":
        return
    if _SETUP_FLAG.exists():
        return

    print("🔧 初回起動を検出しました。セットアップを自動実行します...")
    setup_path = Path(__file__).parent.parent / "scripts" / "setup.py"
    if not setup_path.exists():
        print(f"❌ setup.py が見つかりません: {setup_path}", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run([sys.executable, str(setup_path)], cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print("❌ セットアップに失敗しました。", file=sys.stderr)
        sys.exit(1)

    _SETUP_FLAG.parent.mkdir(parents=True, exist_ok=True)
    _SETUP_FLAG.touch()
    print("\n✅ セットアップ完了。解析を開始します...\n")


# ─── ユーティリティ ───────────────────────────────────────────────────────────

def _scan_inbox() -> list[Path]:
    """inbox フォルダ内の動画ファイルを名前順で返す"""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        f for f in INBOX_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in _VIDEO_EXTS
    )


def _parse_batch_dir_name(name: str) -> dict | None:
    match = _BATCH_DIR_RE.fullmatch(name)
    if not match:
        return None
    return {
        "pattern_name": match.group("pattern"),
        "date": match.group("date"),
        "suffix": int(match.group("suffix") or "1"),
    }


def _normalize_pattern_name(name: str) -> str:
    cleaned = re.sub(r"[\\/]+", "-", name).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = cleaned.strip("._-")
    if not cleaned:
        raise ValueError("パターン名が空です。")
    return cleaned


def _build_batch_dir_name(pattern_name: str, date_token: str, suffix: int | None = None) -> str:
    base = f"{_normalize_pattern_name(pattern_name)}_{date_token}"
    if suffix and suffix > 1:
        return f"{base}_{suffix}"
    return base


def _extract_batch_meta(ts_dir: Path) -> dict:
    parsed = _parse_batch_dir_name(ts_dir.name)
    if parsed is None:
        return {
            "analysis_batch_name": ts_dir.name,
            "pattern_name": None,
            "date": ts_dir.name,
        }
    return {
        "analysis_batch_name": ts_dir.name,
        "pattern_name": parsed["pattern_name"],
        "date": parsed["date"],
    }


def _scan_timestamp_dirs() -> list[Path]:
    """output/ 以下の分析バッチフォルダを新しい順で返す（旧 YYYYMMDD 形式も含む）"""
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    candidates = []
    for directory in OUTPUT_BASE.iterdir():
        if not directory.is_dir():
            continue
        parsed = _parse_batch_dir_name(directory.name)
        if not parsed:
            continue
        candidates.append((parsed["date"], parsed["suffix"], directory.name, directory))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return [item[3] for item in candidates]


def _choose_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n中断しました。")
            sys.exit(0)
        if raw.isdigit() and lo <= int(raw) <= hi:
            return int(raw)
        print(f"  ⚠️  {lo}〜{hi} の番号を入力してください")


def _choose_platform() -> str:
    platforms = ["tiktok", "shorts", "reels"]
    print("\n  プラットフォームを選んでください:")
    for i, p in enumerate(platforms, 1):
        print(f"  [{i}] {p}")
    idx = _choose_int("  番号を入力 > ", 1, len(platforms))
    return platforms[idx - 1]


def _choose_pattern_name(default: str | None = None) -> str:
    prompt = "  パターン名を入力 > "
    if default:
        prompt = f"  パターン名を入力 [{default}] > "
    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n中断しました。")
            sys.exit(0)
        if not raw and default:
            raw = default
        try:
            return _normalize_pattern_name(raw)
        except ValueError:
            print("  ⚠️  パターン名を入力してください")


def _summarize_timestamp_dir(ts_dir: Path) -> str:
    """分析バッチフォルダの概要（動画数・analysis.json数）を返す"""
    video_dirs = [
        d for d in ts_dir.iterdir()
        if d.is_dir() and (d / "analysis.json").exists()
    ]
    meta = _extract_batch_meta(ts_dir)
    label = meta["date"]
    if meta["pattern_name"]:
        label = f"{meta['pattern_name']} / {meta['date']}"
    return f"{len(video_dirs)} 本の analysis.json | {label}"


# ─── 起動フロー選択 ───────────────────────────────────────────────────────────

def _interactive_startup() -> tuple[str, Path, list[Path], str]:
    """
    対話式で起動モードを選ぶ。
    Returns:
        mode: "new" | "use_existing" | "overwrite"
        ts_dir: 対象分析バッチフォルダ
        videos: 解析する動画リスト（use_existing のときは空）
        platform: プラットフォーム文字列
    """
    existing_ts = _scan_timestamp_dirs()

    print("\n" + "═" * 56)
    print("  viral-template-generator — 起動モード選択")
    print("═" * 56)
    print("  [1] 新しく分析する  （パターン名_今日の日付でフォルダを作成）")
    if existing_ts:
        print("  [2] 既存の分析を使う（Phase A の統合分析へスキップ）")
        print("  [3] 既存の分析を上書きする（再解析）")
    print("═" * 56)

    hi = 3 if existing_ts else 1
    choice = _choose_int("  番号を入力 > ", 1, hi)

    # ── [1] 新規 ──────────────────────────────────────────────────────────────
    if choice == 1:
        today = date.today().strftime("%Y%m%d")
        videos = _scan_inbox()
        if not videos:
            print(f"\n❌ 解析できる動画がありません。{INBOX_DIR} に動画を配置してください。")
            sys.exit(1)

        default_pattern = None
        if len(videos) == 1:
            default_pattern = videos[0].stem
        pattern_name = _choose_pattern_name(default_pattern)
        ts_dir = OUTPUT_BASE / _build_batch_dir_name(pattern_name, today)
        # 同日に複数回実行する場合は _2, _3 と連番を付ける
        if ts_dir.exists():
            suffix = 2
            while (OUTPUT_BASE / _build_batch_dir_name(pattern_name, today, suffix)).exists():
                suffix += 1
            ts_dir = OUTPUT_BASE / _build_batch_dir_name(pattern_name, today, suffix)

        print(f"\n  📁 出力フォルダ: {ts_dir.name}")
        print(f"  🎬 解析対象 ({len(videos)} 本):")
        for v in videos:
            print(f"     - {v.name}")

        platform = _choose_platform()
        print(f"\n  ✓ モード: 新規解析 / {platform}\n")
        return "new", ts_dir, videos, platform

    # ── [2] 既存を使う ────────────────────────────────────────────────────────
    if choice == 2:
        ts_dir = _select_timestamp_dir(existing_ts, "使用する")
        print(f"\n  ✓ モード: 既存を使用 → {ts_dir.name}\n")
        return "use_existing", ts_dir, [], ""

    # ── [3] 上書き再解析 ──────────────────────────────────────────────────────
    ts_dir = _select_timestamp_dir(existing_ts, "上書きする")
    videos = _scan_inbox()
    if not videos:
        print(f"\n❌ 解析できる動画がありません。{INBOX_DIR} に動画を配置してください。")
        sys.exit(1)

    print(f"\n  📁 上書き先フォルダ: {ts_dir.name}")
    print(f"  🎬 再解析対象 ({len(videos)} 本):")
    for v in videos:
        print(f"     - {v.name}")

    platform = _choose_platform()
    print(f"\n  ⚠️  既存の analysis.json を上書きします。よろしいですか？ [y/N] ", end="")
    try:
        confirm = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n中断しました。")
        sys.exit(0)
    if confirm != "y":
        print("  中断しました。")
        sys.exit(0)

    print(f"\n  ✓ モード: 上書き再解析 / {platform}\n")
    return "overwrite", ts_dir, videos, platform


def _select_timestamp_dir(existing_ts: list[Path], verb: str) -> Path:
    """既存分析バッチフォルダの一覧を表示して選ばせる"""
    print(f"\n  {verb}分析バッチフォルダを選んでください:")
    print("  " + "─" * 50)
    for i, d in enumerate(existing_ts, 1):
        summary = _summarize_timestamp_dir(d)
        print(f"  [{i}] {d.name}  ({summary})")
    print("  " + "─" * 50)
    idx = _choose_int("  番号を入力 > ", 1, len(existing_ts))
    return existing_ts[idx - 1]


# ─── 1本の動画を解析 ─────────────────────────────────────────────────────────

def _analyze_one(input_path: Path, ts_dir: Path, platform: str, skip_ocr: bool) -> Path:
    """
    1本の動画を解析して analysis.json を生成する。
    Returns: 生成した analysis.json のパス
    """
    output_dir = ts_dir / input_path.stem
    frames_dir = output_dir / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'─' * 56}")
    print(f"🎬 解析中: {input_path.name}")
    print(f"   platform: {platform}")
    print(f"   出力先  : {output_dir}")
    print(f"{'─' * 56}")

    sys.path.insert(0, str(Path(__file__).parent))

    # Layer 1: 動画構造解析
    print("📹 [1/4] Layer1: 動画構造解析...")
    from layers.video_structure import analyze_video_structure
    video_data = analyze_video_structure(input_path, frames_dir, skip_ocr=skip_ocr)
    print(f"   ✓ カット数     : {len(video_data['video_structure']['cuts'])}")
    print(f"   ✓ 顔検出       : {len(video_data['video_structure']['faces'])} フレーム")
    print(f"   ✓ テキスト領域 : {len(video_data['video_structure']['text_regions'])} 件")

    # Layer 2: 音声解析
    print("\n🎤 [2/4] Layer2: 音声解析 (Whisper)...")
    from layers.speech_analysis import analyze_speech
    speech_data = analyze_speech(input_path, output_dir)
    print(f"   ✓ 発話数 : {len(speech_data.get('transcript', []))} セグメント")
    print(f"   ✓ 話速   : {speech_data.get('words_per_minute', 0)} wpm")

    # Layer 2.5: BGM・効果音解析
    print("\n🎵 [2.5/4] Layer2.5: BGM・効果音解析 (librosa)...")
    from layers.audio_scene import analyze_audio_scene
    audio_scene_data = analyze_audio_scene(output_dir)
    print(f"   ✓ BGM区間     : {len(audio_scene_data.get('bgm_segments', []))} セグメント")
    print(f"   ✓ 効果音      : {len(audio_scene_data.get('sfx_events', []))} 件")
    print(f"   ✓ テンポ      : {audio_scene_data.get('dominant_tempo', 0)} BPM")
    print(f"   ✓ BGMカバー率 : {audio_scene_data.get('music_coverage', 0) * 100:.0f}%")

    # Layer 3: バズ構造解析
    print("\n🔥 [3/4] Layer3: バズ構造解析...")
    from layers.viral_pattern import analyze_viral_pattern
    viral_data = analyze_viral_pattern(video_data, speech_data)
    print(f"   ✓ フック              : {viral_data.get('hook_type', 'unknown')} @ {viral_data.get('hook_time', 0):.1f}s")
    print(f"   ✓ パターンインタラプト: {len(viral_data.get('pattern_interrupts', []))} 箇所")
    print(f"   ✓ 情報密度            : {viral_data.get('information_density', 'unknown')}")

    # Layer 4: 字幕ビジュアルスタイル解析
    print("\n🎨 [4/4] Layer4: 字幕ビジュアルスタイル解析...")
    from layers.subtitle_visual import (
        analyze_subtitle_visual_style,
        export_subtitle_style_review_assets,
    )
    import cv2 as _cv2
    _cap4 = _cv2.VideoCapture(str(input_path))
    _res = video_data.get("resolution", {})
    subtitle_visual_data = analyze_subtitle_visual_style(
        _cap4,
        video_data["fps"],
        video_data["video_structure"].get("text_regions", []),
        video_width=_res.get("width", 1080),
        video_height=_res.get("height", 1920),
    )
    subtitle_style_review = export_subtitle_style_review_assets(
        _cap4,
        video_data["fps"],
        video_data["video_structure"].get("cuts", []),
        video_data["video_structure"].get("text_regions", []),
        video_width=_res.get("width", 1080),
        video_height=_res.get("height", 1920),
        output_dir=output_dir,
        source_video=str(input_path),
    )
    _cap4.release()
    subtitle_visual_data["analysis_mode"] = "agent_review_preferred"
    subtitle_visual_data["agent_review"] = subtitle_style_review
    print(f"   ✓ 文字色              : {subtitle_visual_data.get('text_color_hex', '?')}")
    print(f"   ✓ 縁取り              : {'あり ' + str(subtitle_visual_data.get('stroke_width_px', 0)) + 'px' if subtitle_visual_data.get('stroke_detected') else 'なし'}")
    print(f"   ✓ グロー              : {'あり' if subtitle_visual_data.get('glow_detected') else 'なし'}")
    print(f"   ✓ 座布団              : {'あり' if subtitle_visual_data.get('background_box_detected') else 'なし'}")
    print(f"   ✓ 行ごと色違い        : {'あり' if subtitle_visual_data.get('multicolor_lines') else 'なし'}")
    print(f"   ✓ フォントサイズ推定  : {subtitle_visual_data.get('font_size_px', 0)}px (信頼度: {subtitle_visual_data.get('confidence', '?')})")
    print(f"   ✓ レビュー用スクショ  : {subtitle_style_review.get('sample_count', 0)} 枚")
    if subtitle_style_review.get("review_template_path"):
        print(f"   ✓ レビュー雛形        : {subtitle_style_review.get('review_template_path')}")

    # analysis.json 生成
    batch_meta = _extract_batch_meta(ts_dir)
    analysis = {
        "duration": video_data["duration"],
        "fps": video_data["fps"],
        "platform": platform,
        "source_file": str(input_path),
        "analyzed_date": batch_meta["date"],
        "analysis_batch_name": batch_meta["analysis_batch_name"],
        "pattern_name": batch_meta["pattern_name"],
        "resolution": video_data.get("resolution", {}),
        "video_structure": video_data["video_structure"],
        "speech_structure": speech_data,
        "audio_scene": audio_scene_data,
        "viral_structure": viral_data,
        "subtitle_visual": subtitle_visual_data,
    }

    output_path = output_dir / "analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ 完了: {output_path}")
    return output_path


# ─── メイン ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ショート動画を解析して analysis.json を生成します"
    )
    parser.add_argument(
        "input", nargs="?", default=None,
        help="解析する動画ファイルのパス（省略すると対話モード）"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="inbox の全動画を一括解析する"
    )
    parser.add_argument(
        "--platform", choices=["tiktok", "shorts", "reels"], default=None,
        help="対象プラットフォーム（省略すると選択プロンプト）"
    )
    parser.add_argument(
        "--date", default=None,
        help="日付トークン（例: 20260311）。省略すると今日の日付"
    )
    parser.add_argument(
        "--pattern-name", default=None,
        help="分析バッチのパターン名。出力フォルダは [pattern-name]_[date] になる"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="[後方互換] 出力ディレクトリを直接指定する（非推奨）"
    )
    parser.add_argument(
        "--skip-ocr", action="store_true",
        help="OCRをスキップ（高速化・pytesseract未インストール時）"
    )
    args = parser.parse_args()

    _ensure_setup()

    # ── 後方互換: --output-dir が指定された場合は旧動作（単体解析）─────────
    if args.output_dir:
        if args.input is None:
            print("❌ --output-dir を使う場合は input パスを指定してください", file=sys.stderr)
            sys.exit(1)
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            print(f"❌ ファイルが見つかりません: {input_path}", file=sys.stderr)
            sys.exit(1)
        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        # 旧動作: ts_dir を output_dir の親として扱う
        ts_dir = output_dir.parent
        platform = args.platform or "shorts"
        _analyze_one(input_path, ts_dir, platform, args.skip_ocr)
        _notify("viral-template-generator ✅", f"{input_path.name} の解析が完了しました", sound="Glass")
        return

    # ── 非対話モード（--all または input 直接指定）────────────────────────────
    if args.input is not None or args.all:
        platform = args.platform or "shorts"

        if args.all:
            videos = _scan_inbox()
            if not videos:
                print(f"❌ 解析できる動画がありません。{INBOX_DIR} に動画を配置してください。")
                sys.exit(1)
            if not args.pattern_name:
                print("❌ --all を使う場合は --pattern-name を指定してください。", file=sys.stderr)
                sys.exit(1)
        else:
            input_path = Path(args.input).resolve()
            if not input_path.exists():
                print(f"❌ ファイルが見つかりません: {input_path}", file=sys.stderr)
                sys.exit(1)
            videos = [input_path]

        date_token = args.date or date.today().strftime("%Y%m%d")
        pattern_name = args.pattern_name or videos[0].stem
        ts_dir = OUTPUT_BASE / _build_batch_dir_name(pattern_name, date_token)
        ts_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n🚀 一括解析モード | フォルダ: {ts_dir.name} | {len(videos)} 本")
        for i, v in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}] {v.name}")
            _analyze_one(v, ts_dir, platform, args.skip_ocr)

        _notify(
            "viral-template-generator ✅",
            f"全 {len(videos)} 本の解析が完了しました → {ts_dir.name}",
            sound="Glass",
        )
        print(f"\n🎉 全 {len(videos)} 本の解析完了！")
        print(f"   出力フォルダ: {ts_dir}")
        print(f"\n次のステップ: Claude Code に「統合分析して」と伝えてください\n")
        return

    # ── 対話モード ────────────────────────────────────────────────────────────
    _notify("viral-template-generator", "起動モードを選んでください", sound="Ping")
    mode, ts_dir, videos, platform = _interactive_startup()

    if mode == "use_existing":
        # 既存を使う場合は解析せずに終了（Claude が Phase A を担当する）
        print(f"✅ 既存フォルダを使用します: {ts_dir}")
        print(f"\n次のステップ: Claude Code に「{ts_dir.name} の分析ファイルを統合分析して」と伝えてください\n")
        return

    # 新規 or 上書きの場合は全動画を解析
    ts_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n🚀 {len(videos)} 本の解析を開始します...\n")

    completed = []
    failed = []
    for i, v in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}]")
        try:
            out = _analyze_one(v, ts_dir, platform, args.skip_ocr)
            completed.append(out)
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            failed.append(v.name)

    # 完了サマリー
    print(f"\n{'═' * 56}")
    print(f"  🎉 解析完了サマリー")
    print(f"{'═' * 56}")
    print(f"  ✅ 成功: {len(completed)} 本")
    if failed:
        print(f"  ❌ 失敗: {len(failed)} 本")
        for f in failed:
            print(f"     - {f}")
    print(f"  📁 出力フォルダ: {ts_dir}")
    print(f"{'═' * 56}")

    _notify(
        "viral-template-generator ✅",
        f"解析完了 {len(completed)}/{len(videos)} 本 → {ts_dir.name}",
        sound="Glass",
    )
    print(f"\n次のステップ: Claude Code に「統合分析して」と伝えてください\n")


if __name__ == "__main__":
    main()
