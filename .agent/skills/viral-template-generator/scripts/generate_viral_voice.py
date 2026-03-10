#!/usr/bin/env python3
"""
generate_viral_voice: script.md をセクション別に VOICEVOX で音声化し、
remotion/public/audio/ に配置する。

VOICEVOX が未起動の場合は自動起動を試みる。

Usage:
  python3 generate_viral_voice.py \
    --script [script.mdの絶対パス] \
    --output-dir [remotion/public/audioの絶対パス] \
    --profile narrator_female
"""
import argparse
import io
import json
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("requests が見つかりません。pip install requests でインストールしてください。")

VOICEVOX_BASE = "http://127.0.0.1:50021"

COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_repo_root

PROJECT_ROOT = get_repo_root()
CONFIG_FILE = PROJECT_ROOT / "Remotion" / "configs" / "voice_config.json"

# ─── VOICEVOX 起動確認 & 自動起動 ───────────────────────────────────────────

def is_voicevox_running() -> bool:
    try:
        r = requests.get(f"{VOICEVOX_BASE}/version", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def start_voicevox() -> bool:
    """VOICEVOX を OS に応じて起動し、最大30秒待つ"""
    print("VOICEVOX が起動していません。自動起動を試みます...")

    if sys.platform == "darwin":
        # macOS: 一般的なインストール先を試みる
        candidates = [
            Path("/Applications/VOICEVOX.app"),
            Path.home() / "Applications" / "VOICEVOX.app",
        ]
        launched = False
        for app in candidates:
            if app.exists():
                subprocess.Popen(["open", str(app)])
                launched = True
                break
        if not launched:
            # open -a でアプリ名で試みる
            result = subprocess.run(["open", "-a", "VOICEVOX"], capture_output=True)
            if result.returncode != 0:
                print("  → VOICEVOX アプリが見つかりませんでした。手動で起動してください。")
                print("     起動後に Enter を押してください。")
                input()
                return is_voicevox_running()
    elif sys.platform == "win32":
        candidates = [
            Path("C:/Users") / Path.home().name / "AppData/Local/Programs/VOICEVOX/VOICEVOX.exe",
            Path("C:/Program Files/VOICEVOX/VOICEVOX.exe"),
        ]
        launched = False
        for exe in candidates:
            if exe.exists():
                subprocess.Popen([str(exe)])
                launched = True
                break
        if not launched:
            print("  → VOICEVOX.exe が見つかりませんでした。手動で起動してください。")
            print("     起動後に Enter を押してください。")
            input()
            return is_voicevox_running()
    else:
        print("  → Linux では手動で VOICEVOX を起動してください。")
        print("     起動後に Enter を押してください。")
        input()
        return is_voicevox_running()

    print("  VOICEVOX 起動待ち...", end="", flush=True)
    for _ in range(30):
        time.sleep(1)
        print(".", end="", flush=True)
        if is_voicevox_running():
            print(" 起動完了！")
            return True
    print(" タイムアウト。手動で起動後に Enter を押してください。")
    input()
    return is_voicevox_running()


def ensure_voicevox() -> bool:
    if is_voicevox_running():
        return True
    return start_voicevox()


# ─── VOICEVOX API ────────────────────────────────────────────────────────────

def get_speaker_id(speaker_name: str, style_name: str) -> int | None:
    """スピーカー名 + スタイル名から speaker_id を取得する"""
    r = requests.get(f"{VOICEVOX_BASE}/speakers", timeout=10)
    speakers = r.json()
    for sp in speakers:
        if sp["name"] == speaker_name:
            for style in sp["styles"]:
                if style["name"] == style_name:
                    return style["id"]
    return None


def synthesize(
    text: str,
    speaker_id: int,
    speed: float = 1.0,
    pitch: float = 0.0,
    volume: float = 1.0,
    pause_length_scale: float = 1.0,
    post_phoneme_length: float = 0.1,
) -> bytes:
    """テキストを WAV バイト列に変換する"""
    # audio_query 生成
    query_resp = requests.post(
        f"{VOICEVOX_BASE}/audio_query",
        params={"text": text, "speaker": speaker_id},
        timeout=30,
    )
    query_resp.raise_for_status()
    query = query_resp.json()

    # パラメータ上書き
    query["speedScale"] = speed
    query["pitchScale"] = pitch
    query["volumeScale"] = volume
    query["pauseLengthScale"] = pause_length_scale
    query["postPhonemeLength"] = post_phoneme_length

    # 音声合成
    synth_resp = requests.post(
        f"{VOICEVOX_BASE}/synthesis",
        params={"speaker": speaker_id},
        json=query,
        timeout=60,
    )
    synth_resp.raise_for_status()
    return synth_resp.content


def wav_bytes_to_wave(data: bytes) -> wave.Wave_read:
    return wave.open(io.BytesIO(data))


def concat_wavs(wav_data_list: list[bytes]) -> bytes:
    """複数の WAV バイト列を結合して1つの WAV バイト列を返す"""
    if not wav_data_list:
        return b""
    if len(wav_data_list) == 1:
        return wav_data_list[0]

    buf = io.BytesIO()
    out_wav = None
    for data in wav_data_list:
        w = wave.open(io.BytesIO(data))
        if out_wav is None:
            out_wav = wave.open(buf, "wb")
            out_wav.setnchannels(w.getnchannels())
            out_wav.setsampwidth(w.getsampwidth())
            out_wav.setframerate(w.getframerate())
        out_wav.writeframes(w.readframes(w.getnframes()))
        w.close()
    if out_wav:
        out_wav.close()
    return buf.getvalue()


def get_wav_duration(wav_data: bytes) -> float:
    with wave.open(io.BytesIO(wav_data)) as wav_file:
        return wav_file.getnframes() / wav_file.getframerate()


def render_sections(
    sections: list[dict],
    speaker_id: int,
    settings: dict[str, float],
) -> tuple[list[dict], float]:
    rendered_sections: list[dict] = []
    total_duration = 0.0

    for i, sec in enumerate(sections):
        wav_data = synthesize(
            sec["text"],
            speaker_id,
            speed=settings["speed"],
            pitch=settings["pitch"],
            volume=settings["volume"],
            pause_length_scale=settings["pause_length_scale"],
            post_phoneme_length=settings["post_phoneme_length"],
        )
        duration = get_wav_duration(wav_data)
        rendered_sections.append(
            {
                "slot": f"{i:02d}_{sec['key']}",
                "text": sec["text"],
                "wav_data": wav_data,
                "duration": duration,
            }
        )
        total_duration += duration

    return rendered_sections, total_duration


def infer_target_seconds(script_path: Path) -> float | None:
    subtitles_path = script_path.with_name("subtitles.json")
    if not subtitles_path.exists():
        return None

    try:
        data = json.loads(subtitles_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    total_seconds = data.get("total_duration_seconds")
    if isinstance(total_seconds, (int, float)):
        return float(total_seconds)
    return None


# ─── script.md パーサー ───────────────────────────────────────────────────────

SECTION_PATTERNS = [
    ("hook",    r"##\s*フック"),
    ("opening", r"##\s*予告"),
    ("s1",      r"##\s*本編\s*セクション1"),
    ("s2",      r"##\s*本編\s*セクション2"),
    ("s3",      r"##\s*本編\s*セクション3"),
    ("cta",     r"##\s*アウトロ|##\s*CTA"),
]


def parse_script(script_path: Path) -> list[dict]:
    """
    script.md を読んで各セクションの {"key": str, "text": str} リストを返す。
    演出メモ・ヘッダー・空行を除去してナレーション本文のみ抽出する。
    """
    text = script_path.read_text(encoding="utf-8")
    # 演出メモセクションを削除
    text = re.sub(r"##\s*演出メモ.*", "", text, flags=re.DOTALL)

    sections = []
    for key, pattern in SECTION_PATTERNS:
        # | の優先順位対策で非キャプチャグループで囲む
        match = re.search(
            r"(?:" + pattern + r")[^\n]*\n+(.*?)(?=\n##|\Z)",
            text, re.DOTALL
        )
        if not match:
            continue
        body = match.group(1)
        # --- 区切り、空行、コメント行を除去
        lines = [
            l.strip() for l in body.splitlines()
            if l.strip() and not l.strip().startswith("---") and not l.strip().startswith("#")
        ]
        narration = "。".join(lines) if lines else ""
        # 読点・句点の連続を整理
        narration = re.sub(r"[。、]{2,}", "。", narration)
        if narration:
            sections.append({"key": key, "text": narration})

    return sections


# ─── メイン処理 ──────────────────────────────────────────────────────────────

def run(
    script_path: Path,
    output_dir: Path,
    profile_name: str,
    target_seconds: float | None,
):
    # 1. VOICEVOX 起動確認
    if not ensure_voicevox():
        raise SystemExit("VOICEVOX に接続できませんでした。")

    # 2. 設定読み込み
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    profile = config.get(profile_name)
    if not profile:
        raise SystemExit(f"プロファイル '{profile_name}' が voice_config.json に見つかりません。\n"
                         f"利用可能: {list(config.keys())}")

    speaker_id = get_speaker_id(profile["speaker_name"], profile["style_name"])
    if speaker_id is None:
        raise SystemExit(f"スピーカー '{profile['speaker_name']} / {profile['style_name']}' が見つかりません。")

    print(f"スピーカー: {profile['speaker_name']} / {profile['style_name']} (id={speaker_id})")

    # 3. script.md パース
    sections = parse_script(script_path)
    if not sections:
        raise SystemExit("script.md からナレーション本文を取得できませんでした。")

    print(f"\n音声化セクション: {len(sections)}件")
    if target_seconds is not None:
        print(f"目標尺: {target_seconds:.1f}秒")

    # 4. 出力ディレクトリ作成
    output_dir.mkdir(parents=True, exist_ok=True)

    base_settings = {
        "speed": float(profile.get("speed", 1.0)),
        "pitch": float(profile.get("pitch", 0.0)),
        "volume": float(profile.get("volume", 1.0)),
        "pause_length_scale": float(profile.get("pause_length_scale", 1.0)),
        "post_phoneme_length": float(profile.get("post_phoneme_length", 0.1)),
    }
    applied_settings = dict(base_settings)

    rendered_sections, duration = render_sections(sections, speaker_id, applied_settings)

    if target_seconds and abs(duration - target_seconds) / target_seconds > 0.02:
        ratio = duration / target_seconds
        adjusted_settings = dict(base_settings)
        adjusted_settings["speed"] = min(1.8, max(0.6, base_settings["speed"] * ratio))
        adjusted_settings["pause_length_scale"] = min(
            2.5,
            max(0.4, base_settings["pause_length_scale"] / ratio),
        )
        adjusted_settings["post_phoneme_length"] = min(
            0.3,
            max(0.02, base_settings["post_phoneme_length"] / ratio),
        )
        print(
            "\n目標尺に合わせて再合成します: "
            f"speed={adjusted_settings['speed']:.2f}, "
            f"pause={adjusted_settings['pause_length_scale']:.2f}, "
            f"post={adjusted_settings['post_phoneme_length']:.2f}"
        )
        rendered_sections, duration = render_sections(sections, speaker_id, adjusted_settings)
        applied_settings = adjusted_settings

    # 5. セクションごとに書き出し
    all_wav_data = []
    for section in rendered_sections:
        slot = section["slot"]
        text = section["text"]
        print(
            f"  [{slot}] {text[:30]}{'...' if len(text) > 30 else ''}"
            f" ({section['duration']:.2f}s)",
            end="",
            flush=True,
        )
        out_file = output_dir / f"{slot}.wav"
        out_file.write_bytes(section["wav_data"])
        all_wav_data.append(section["wav_data"])
        print(f" → {out_file.name}")

    # 6. 全セクションを結合して narration.wav を生成
    print("\n全セクションを結合中...", end="", flush=True)
    narration = concat_wavs(all_wav_data)
    narration_path = output_dir / "narration.wav"
    narration_path.write_bytes(narration)
    print(f" → {narration_path}")

    # 7. WAV の長さを確認
    with wave.open(str(narration_path)) as w:
        duration = w.getnframes() / w.getframerate()
    print(f"\n音源長: {duration:.1f}秒")
    if target_seconds is not None:
        print(f"差分: {duration - target_seconds:+.1f}秒")
    print(
        "適用設定: "
        f"speed={applied_settings['speed']:.2f}, "
        f"pause={applied_settings['pause_length_scale']:.2f}, "
        f"post={applied_settings['post_phoneme_length']:.2f}"
    )

    print("\n完了！")
    print(f"出力先: {output_dir}")
    print("次のステップ: ViralVideo.tsx に Audio トラックを追加してください。")
    print("""
追加コード（ViralVideo.tsx の return 内に挿入）:
  import { Audio } from "remotion";
  <Sequence from={0} durationInFrames={totalFrames}>
    <Audio src={staticFile("audio/narration.wav")} volume={1.0} />
  </Sequence>
""")


def main():
    parser = argparse.ArgumentParser(description="script.md を VOICEVOX で音声化")
    parser.add_argument("--script", "-s", type=Path, required=False,
                        help="script.md の絶対パス")
    parser.add_argument("--output-dir", "-o", type=Path, required=False,
                        help="出力先ディレクトリ（例: remotion/public/audio）")
    parser.add_argument("--profile", "-p", type=str, default="narrator_female",
                        help="voice_config.json のプロファイル名 (default: narrator_female)")
    parser.add_argument("--target-seconds", type=float, default=None,
                        help="目標尺（秒）。省略時は隣接する subtitles.json から自動推定")
    args = parser.parse_args()

    # script パスの決定
    if args.script:
        script_path = args.script
    else:
        candidates = list(PROJECT_ROOT.rglob("script.md"))
        candidates = [c for c in candidates if "node_modules" not in str(c)]
        if not candidates:
            raise SystemExit("script.md が見つかりません。--script で指定してください。")
        if len(candidates) == 1:
            script_path = candidates[0]
            print(f"台本: {script_path}")
        else:
            for i, c in enumerate(candidates):
                print(f"  [{i}] {c}")
            idx = int(input("番号を選択: "))
            script_path = candidates[idx]

    # output-dir の決定
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # script.md と同じ出力タイトルフォルダの remotion/public/audio に自動配置
        output_dir = script_path.parent / "remotion" / "public" / "audio"

    target_seconds = args.target_seconds
    if target_seconds is None:
        target_seconds = infer_target_seconds(script_path)

    run(script_path, output_dir, args.profile, target_seconds)


if __name__ == "__main__":
    main()
