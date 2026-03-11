#!/usr/bin/env python3
"""
analyze-video: ショート動画3層解析 → analysis.json 生成

Usage:
  # ファイル引数なし → inbox フォルダを一覧表示して選択
  python3 analyze_video.py

  # ファイルを直接指定
  python3 analyze_video.py /path/to/input.mp4 --platform tiktok
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_config_dir, get_repo_root

# ─── パス定数 ─────────────────────────────────────────────────────────────────
PROJECT_ROOT = get_repo_root()

# 動画置き場（ここに .mp4 を置いておく）
INBOX_DIR = PROJECT_ROOT / "inputs" / "viral-analysis"

# 解析結果の出力先ベース（動画ごとにサブフォルダが作られる）
OUTPUT_BASE = PROJECT_ROOT / "outputs" / "viral-analysis"

# セットアップ完了フラグ（git 管理外・ホームディレクトリ配下）
_SETUP_FLAG = get_config_dir("viral-template-generator") / ".setup_done"

# 対応動画拡張子
_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


# ─── クロスプラットフォーム通知 ──────────────────────────────────────────────

def _notify(title: str, message: str, sound: str = "Ping") -> None:
    """OS に応じた通知センター通知 + サウンド（他作業中でも気づけるように）

    - macOS  : osascript（通知センター + サウンド）
    - Linux  : notify-send（libnotify）+ ターミナルベル
    - Windows: PowerShell BalloonTip（タスクトレイ）+ console beep
    """
    if sys.platform == "darwin":
        # macOS: 通知センター + サウンド
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
        # Linux: notify-send (libnotify) + ターミナルベル
        try:
            subprocess.run(
                ["notify-send", "--app-name", title, title, message],
                capture_output=True,
                check=False,
            )
        except OSError:
            pass
        print("\a", end="", flush=True)

    elif sys.platform == "win32":
        # Windows: PowerShell タスクトレイ BalloonTip + beep
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
                capture_output=True,
                check=False,
            )
        except OSError:
            print("\a", end="", flush=True)

    else:
        # フォールバック: ターミナルベルのみ
        print("\a", end="", flush=True)


# ─── セットアップ自動実行 ─────────────────────────────────────────────────────

def _ensure_setup() -> None:
    """セットアップ済みか確認し、未完了なら自動でセットアップを実行する。"""
    # Docker ランタイムはビルド時点で依存が固定されているため、
    # 実行時セットアップとホーム配下のフラグ書き込みを省略する。
    if os.environ.get("TEAM_INFO_IN_DOCKER") == "1":
        return

    if _SETUP_FLAG.exists():
        return

    print("🔧 初回起動を検出しました。セットアップを自動実行します...")
    print(f"   (フラグ: {_SETUP_FLAG})\n")

    setup_path = Path(__file__).parent.parent / "scripts" / "setup.py"
    if not setup_path.exists():
        print(f"❌ setup.py が見つかりません: {setup_path}", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run([sys.executable, str(setup_path)], cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print("❌ セットアップに失敗しました。setup.py を確認してください。", file=sys.stderr)
        sys.exit(1)

    if not _SETUP_FLAG.exists():
        _SETUP_FLAG.parent.mkdir(parents=True, exist_ok=True)
        _SETUP_FLAG.touch()

    print("\n✅ セットアップ完了。解析を開始します...\n")


# ─── 動画選択 ─────────────────────────────────────────────────────────────────

def _scan_inbox() -> list[Path]:
    """inbox フォルダ内の動画ファイルを名前順で返す"""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        f for f in INBOX_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in _VIDEO_EXTS
    )


def _select_video() -> tuple[Path, str]:
    """
    inbox フォルダの動画一覧を表示し、ユーザーに選択させる。
    通知 + サウンドで他作業中でも気づけるようにする。
    Returns: (選択したファイルのPath, プラットフォーム文字列)
    """
    videos = _scan_inbox()

    if not videos:
        print(f"\n❌ 解析できる動画がありません。")
        print(f"   以下のフォルダに .mp4 / .mov などを配置してください:")
        print(f"   {INBOX_DIR}\n")
        sys.exit(1)

    # ── 動画一覧を表示 ─────────────────────────────────────────────────────
    print("\n" + "─" * 52)
    print("  viral-template-generator")
    print("─" * 52)
    print(f"  inbox: {INBOX_DIR}")
    print("─" * 52)
    for i, v in enumerate(videos, 1):
        size_mb = v.stat().st_size / 1024 / 1024
        print(f"  [{i}] {v.name:<40} {size_mb:>6.1f} MB")
    print("─" * 52)

    # ── 通知を送って選択を促す ────────────────────────────────────────────
    _notify(
        "viral-template-generator",
        f"解析する動画を選んでください（{len(videos)} 件）",
        sound="Ping",
    )

    # ── 動画番号の選択 ────────────────────────────────────────────────────
    while True:
        try:
            raw = input("  解析する動画の番号を入力 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n中断しました。")
            sys.exit(0)
        if raw.isdigit() and 1 <= int(raw) <= len(videos):
            selected = videos[int(raw) - 1]
            break
        print(f"  ⚠️  1〜{len(videos)} の番号を入力してください")

    # ── プラットフォームの選択 ────────────────────────────────────────────
    platforms = ["tiktok", "shorts", "reels"]
    print("\n  プラットフォームを選んでください:")
    for i, p in enumerate(platforms, 1):
        print(f"  [{i}] {p}")

    _notify(
        "viral-template-generator",
        "プラットフォームを選んでください",
        sound="Tink",
    )

    while True:
        try:
            raw = input("  番号を入力 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n中断しました。")
            sys.exit(0)
        if raw.isdigit() and 1 <= int(raw) <= len(platforms):
            platform = platforms[int(raw) - 1]
            break
        print(f"  ⚠️  1〜{len(platforms)} の番号を入力してください")

    print(f"\n  ✓ 選択: {selected.name}  /  {platform}\n")
    return selected, platform


# ─── メイン ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ショート動画を解析して analysis.json を生成します"
    )
    parser.add_argument(
        "input", nargs="?", default=None,
        help="解析する動画ファイルのパス（省略すると inbox から選択）"
    )
    parser.add_argument(
        "--platform", choices=["tiktok", "shorts", "reels"], default=None,
        help="対象プラットフォーム（省略すると選択プロンプトが出る）"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="出力ディレクトリ（省略すると outputs/viral-analysis/{動画名}/ になる）"
    )
    parser.add_argument(
        "--skip-ocr", action="store_true",
        help="OCRをスキップ（高速化・pytesseract未インストール時）"
    )
    args = parser.parse_args()

    # ── セットアップ確認（未完了なら自動実行） ──────────────────────────────
    _ensure_setup()

    # ── 動画・プラットフォームの決定 ─────────────────────────────────────────
    if args.input is None:
        # 引数なし → inbox から対話選択
        input_path, platform = _select_video()
    else:
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            print(f"❌ ファイルが見つかりません: {input_path}", file=sys.stderr)
            sys.exit(1)
        platform = args.platform or "tiktok"

    # ── 出力ディレクトリ決定（動画名ごとにサブフォルダ） ──────────────────
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        output_dir = OUTPUT_BASE / input_path.stem

    frames_dir = output_dir / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎬 viral-template-generator 解析開始")
    print(f"   入力    : {input_path.name}")
    print(f"   platform: {platform}")
    print(f"   出力先  : {output_dir}\n")

    sys.path.insert(0, str(Path(__file__).parent))

    # ── Layer 1: 動画構造解析 ────────────────────────────────────────────
    print("📹 [1/3] Layer1: 動画構造解析...")
    from layers.video_structure import analyze_video_structure
    video_data = analyze_video_structure(input_path, frames_dir, skip_ocr=args.skip_ocr)
    print(f"   ✓ カット数     : {len(video_data['video_structure']['cuts'])}")
    print(f"   ✓ 顔検出       : {len(video_data['video_structure']['faces'])} フレーム")
    print(f"   ✓ テキスト領域 : {len(video_data['video_structure']['text_regions'])} 件")

    # ── Layer 2: 音声解析 ────────────────────────────────────────────────
    print("\n🎤 [2/3] Layer2: 音声解析 (Whisper)...")
    from layers.speech_analysis import analyze_speech
    speech_data = analyze_speech(input_path, output_dir)
    print(f"   ✓ 発話数 : {len(speech_data.get('transcript', []))} セグメント")
    print(f"   ✓ 話速   : {speech_data.get('words_per_minute', 0)} wpm")

    # ── Layer 2.5: BGM・効果音解析 ──────────────────────────────────────
    print("\n🎵 [2.5/3] Layer2.5: BGM・効果音解析 (librosa)...")
    from layers.audio_scene import analyze_audio_scene
    audio_scene_data = analyze_audio_scene(output_dir)
    print(f"   ✓ BGM区間     : {len(audio_scene_data.get('bgm_segments', []))} セグメント")
    print(f"   ✓ 効果音      : {len(audio_scene_data.get('sfx_events', []))} 件")
    print(f"   ✓ テンポ      : {audio_scene_data.get('dominant_tempo', 0)} BPM")
    print(f"   ✓ BGMカバー率 : {audio_scene_data.get('music_coverage', 0) * 100:.0f}%")

    # ── Layer 3: バズ構造解析 ────────────────────────────────────────────
    print("\n🔥 [3/4] Layer3: バズ構造解析...")
    from layers.viral_pattern import analyze_viral_pattern
    viral_data = analyze_viral_pattern(video_data, speech_data)
    print(f"   ✓ フック              : {viral_data.get('hook_type', 'unknown')} @ {viral_data.get('hook_time', 0):.1f}s")
    print(f"   ✓ パターンインタラプト: {len(viral_data.get('pattern_interrupts', []))} 箇所")
    print(f"   ✓ 情報密度            : {viral_data.get('information_density', 'unknown')}")

    # ── Layer 4: 字幕ビジュアルスタイル解析 ─────────────────────────────
    print("\n🎨 [4/4] Layer4: 字幕ビジュアルスタイル解析...")
    from layers.subtitle_visual import analyze_subtitle_visual_style
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
    _cap4.release()
    print(f"   ✓ 文字色              : {subtitle_visual_data.get('text_color_hex', '?')}")
    print(f"   ✓ 縁取り              : {'あり ' + str(subtitle_visual_data.get('stroke_width_px', 0)) + 'px' if subtitle_visual_data.get('stroke_detected') else 'なし'}")
    print(f"   ✓ グロー              : {'あり' if subtitle_visual_data.get('glow_detected') else 'なし'}")
    print(f"   ✓ 座布団              : {'あり ' + str(subtitle_visual_data.get('background_box_rgba', '')) if subtitle_visual_data.get('background_box_detected') else 'なし'}")
    print(f"   ✓ 行ごと色違い        : {'あり' if subtitle_visual_data.get('multicolor_lines') else 'なし'}")
    print(f"   ✓ フォントサイズ推定  : {subtitle_visual_data.get('font_size_px', 0)}px (信頼度: {subtitle_visual_data.get('confidence', '?')})")

    # ── analysis.json 生成 ───────────────────────────────────────────────
    analysis = {
        "duration": video_data["duration"],
        "fps": video_data["fps"],
        "platform": platform,
        "source_file": str(input_path),
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

    # ── 完了通知 ─────────────────────────────────────────────────────────
    _notify(
        "viral-template-generator ✅",
        f"{input_path.name} の解析が完了しました",
        sound="Glass",
    )

    print(f"\n✅ analysis.json 生成完了: {output_path}")
    print("\n次のステップ: Claude Code に以下を伝えてください")
    print(f'  「{output_path} からRemotionテンプレートを生成して」\n')


if __name__ == "__main__":
    main()
