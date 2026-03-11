#!/usr/bin/env python3
"""
fetch_bgm_sfx: viral_patterns.md の分析結果に基づいて BGM と SFX を用意する。

BGM  : ccMixter API (認証不要, CC ライセンス) を優先し、
       失敗時はローカル生成 BGM にフォールバックする
SFX  : ローカル合成を既定とし、オプションで Freesound API も利用可

Usage:
  python3 fetch_bgm_sfx.py --output-dir [remotion/public/audioの絶対パス]
  python3 fetch_bgm_sfx.py --output-dir [path] --viral-patterns [viral_patterns.mdのパス]
  python3 fetch_bgm_sfx.py --output-dir [path] --freesound-key YOUR_KEY
"""
import argparse
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# macOS では Python のデフォルト SSL コンテキストが証明書を見つけられない場合がある
_SSL_CTX = ssl.create_default_context()
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX.check_hostname = False
    _SSL_CTX.verify_mode = ssl.CERT_NONE

SKILL_DIR = Path(__file__).resolve().parent
SFX_CATALOG = SKILL_DIR / "assets" / "sfx_catalog.json"

COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_repo_root

PROJECT_ROOT = get_repo_root()

UA = "viral-template-generator/1.0"


def http_get(url: str, params: dict = None) -> bytes:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20, context=_SSL_CTX) as r:
        return r.read()


def http_download(url: str, dest: Path) -> bool:
    try:
        data = http_get(url)
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"    ダウンロード失敗: {e}")
        return False


# ─── viral_patterns.md パーサー ───────────────────────────────────────────────

def _dedupe_preserve_order(values: list[float]) -> list[float]:
    seen: set[float] = set()
    result: list[float] = []
    for value in values:
        rounded = round(value, 3)
        if rounded in seen:
            continue
        seen.add(rounded)
        result.append(rounded)
    return result


def _extract_interrupt_times(text: str) -> list[float]:
    cluster_matches = re.findall(r"平均\s*(\d+(?:\.\d+)?)秒付近", text)
    if cluster_matches:
        return _dedupe_preserve_order([float(value) for value in cluster_matches])

    recommended_match = re.search(
        r"セクション境界（([\d.]+)秒・([\d.]+)秒・([\d.]+)秒付近）",
        text,
    )
    if recommended_match:
        return [float(recommended_match.group(i)) for i in range(1, 4)]

    times = re.findall(r"(\d+(?:\.\d+)?)秒", text[:2000])
    return _dedupe_preserve_order([float(value) for value in times if float(value) < 60])


def parse_patterns(patterns_path: Path) -> dict:
    """viral_patterns.md から BGM/SFX 要件を抽出する"""
    text = patterns_path.read_text(encoding="utf-8")
    result = {
        "bpm": 120,
        "tone": "entertainment",
        "energy": "high",
        "sfx_types": ["whoosh", "impact", "transition"],
        "interrupt_times": [3.0, 20.0, 43.0],
        "total_duration_seconds": 54.0,
    }

    # BPM
    bpm_match = re.search(r"平均テンポ\s*[|｜]\s*([\d.]+)\s*BPM", text)
    if bpm_match:
        result["bpm"] = float(bpm_match.group(1))

    # tone
    tone_match = re.search(r"トーン\s*[|｜]\s*(\w+)", text)
    if tone_match:
        result["tone"] = tone_match.group(1)

    # エネルギー傾向
    energy_match = re.search(r"エネルギー傾向\s*[|｜]\s*([\w〜]+)", text)
    if energy_match:
        result["energy"] = energy_match.group(1)

    # SFX タイプ分布
    sfx_types = re.findall(r"\b(whoosh|impact|transition|pop|cut|chime)\b", text)
    if sfx_types:
        result["sfx_types"] = list(dict.fromkeys(sfx_types))

    # パターンインタラプトタイミング
    interrupt_times = _extract_interrupt_times(text)
    if interrupt_times:
        result["interrupt_times"] = interrupt_times

    duration_match = re.search(r"\|\s*動画尺（秒）\s*\|\s*([\d.]+)\s*\|", text)
    if duration_match:
        result["total_duration_seconds"] = float(duration_match.group(1))

    return result


# ─── BGM 取得（ccMixter API, 認証不要） ──────────────────────────────────────

CCMIXTER_API = "https://ccmixter.org/api/query"

TONE_TO_KEYWORDS = {
    "entertainment": "upbeat electronic pop",
    "educational":  "calm instrumental ambient",
    "curiosity":    "mysterious cinematic",
    "general":      "background music",
}

def _mix_sample(current: float, addition: float, gain: float = 1.0) -> float:
    return max(-1.0, min(1.0, current + addition * gain))


def synthesize_bgm(
    tone: str,
    bpm: float,
    duration_seconds: float,
    output_dir: Path,
) -> Path:
    """簡易的な BGM をローカル生成する"""
    framerate = 22050
    total_samples = int(duration_seconds * framerate)
    beat_seconds = 60.0 / bpm
    bar_seconds = beat_seconds * 4
    chord_progressions = {
        "entertainment": [
            (220.0, 330.0, 440.0),
            (246.94, 369.99, 493.88),
            (196.0, 293.66, 392.0),
            (261.63, 392.0, 523.25),
        ],
        "curiosity": [
            (196.0, 233.08, 293.66),
            (174.61, 220.0, 261.63),
            (220.0, 261.63, 329.63),
            (164.81, 220.0, 261.63),
        ],
        "educational": [
            (174.61, 261.63, 349.23),
            (196.0, 293.66, 392.0),
            (220.0, 329.63, 440.0),
            (196.0, 293.66, 392.0),
        ],
    }
    progression = chord_progressions.get(tone, chord_progressions["entertainment"])
    samples: list[float] = []

    for i in range(total_samples):
        t = i / framerate
        bar_index = int(t / bar_seconds) % len(progression)
        beat_in_bar = (t % bar_seconds) / beat_seconds
        beat_index = int(beat_in_bar)
        beat_progress = beat_in_bar - beat_index
        chord = progression[bar_index]
        bass_freq = chord[0] / 2

        sample = 0.0

        pad_env = 0.12 + 0.03 * math.sin(2 * math.pi * 0.25 * t)
        for freq in chord:
            sample = _mix_sample(sample, math.sin(2 * math.pi * freq * t) * pad_env, 0.32)

        bass_env = math.exp(-beat_progress * 3.5) * 0.35
        sample = _mix_sample(sample, math.sin(2 * math.pi * bass_freq * t) * bass_env)

        kick_env = math.exp(-beat_progress * 18) if beat_progress < 0.25 else 0.0
        if kick_env:
            kick_freq = 60 + 50 * math.exp(-beat_progress * 28)
            sample = _mix_sample(sample, math.sin(2 * math.pi * kick_freq * t) * kick_env, 0.9)

        if beat_index in (1, 3) and beat_progress < 0.18:
            clap_env = math.exp(-beat_progress * 26) * 0.18
            clap_noise = math.sin(2 * math.pi * 1800 * t) + math.sin(2 * math.pi * 2400 * t)
            sample = _mix_sample(sample, clap_noise * clap_env, 0.25)

        half_beat_progress = ((t % beat_seconds) / beat_seconds) * 2
        hat_phase = half_beat_progress % 1
        if hat_phase < 0.10:
            hat_env = math.exp(-hat_phase * 35) * 0.08
            hat_noise = math.sin(2 * math.pi * 5000 * t) + math.sin(2 * math.pi * 7200 * t)
            sample = _mix_sample(sample, hat_noise * hat_env, 0.18)

        lead_freq = chord[(beat_index + bar_index) % len(chord)] * 2
        lead_env = (0.10 if beat_progress < 0.55 else 0.04) * (1 - min(1.0, beat_progress * 1.5))
        sample = _mix_sample(sample, math.sin(2 * math.pi * lead_freq * t) * lead_env, 0.4)

        fade_in = min(1.0, t / 0.7)
        fade_out = min(1.0, max(0.0, (duration_seconds - t) / 1.2))
        samples.append(sample * fade_in * fade_out * 0.78)

    output_path = output_dir / "bgm_generated.wav"
    _write_wav(output_path, _samples_to_bytes(samples), framerate=framerate)

    credit = output_dir / "bgm_credit.txt"
    credit.write_text(
        "BGM: Generated locally by fetch_bgm_sfx.py\n"
        "Source: procedural fallback\n"
        "License: project-local generated audio\n",
        encoding="utf-8",
    )
    return output_path


def fetch_bgm(tone: str, bpm: float, output_dir: Path) -> Path | None:
    """ccMixter から BGM を検索・ダウンロードする"""
    keywords = TONE_TO_KEYWORDS.get(tone, "upbeat background")
    print(f"\n[BGM] ccMixter 検索: '{keywords}' (推奨 BPM: {bpm:.0f})")

    try:
        params = {
            "f": "json",
            "limit": 20,
            "q": keywords,
            "lic": "cc",
            "order": "rank",
        }
        data = json.loads(http_get(CCMIXTER_API, params))
    except Exception as e:
        print(f"  ccMixter API エラー: {e}")
        return None

    if not data:
        print("  検索結果が0件でした。")
        return None

    # ダウンロード可能なファイルを順に試みる
    for item in data:
        files = item.get("files", [])
        for f in files:
            url = f.get("download_url") or f.get("file_url", "")
            if not url:
                continue
            ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
            if ext not in (".mp3", ".wav", ".ogg"):
                continue

            dest = output_dir / f"bgm{ext}"
            title = item.get("upload_name", "unknown")
            artist = item.get("artist_name", "unknown")
            license_url = item.get("license_url", "CC")
            print(f"  → {title} by {artist}")
            print(f"    ライセンス: {license_url}")
            print(f"    ダウンロード中...", end="", flush=True)

            if http_download(url, dest):
                print(f" 保存: {dest.name}")
                # クレジットファイルを出力
                credit = output_dir / "bgm_credit.txt"
                credit.write_text(
                    f"BGM: {title}\nArtist: {artist}\nLicense: {license_url}\nSource: ccMixter\n",
                    encoding="utf-8"
                )
                return dest
            else:
                continue

    print("  ダウンロード可能なファイルが見つかりませんでした。")
    return None


# ─── SFX ローカル合成（認証不要・ライセンスフリー） ─────────────────────────

import math
import struct
import wave as _wave_mod

def _write_wav(path: Path, frames: bytes, framerate: int = 44100, channels: int = 1):
    with _wave_mod.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)  # 16bit
        w.setframerate(framerate)
        w.writeframes(frames)


def _samples_to_bytes(samples: list[float]) -> bytes:
    """[-1.0, 1.0] の float リストを 16bit PCM に変換"""
    return struct.pack(f"<{len(samples)}h", *[int(max(-32767, min(32767, s * 32767))) for s in samples])


def _synthesize_whoosh(duration: float = 0.5, framerate: int = 44100) -> bytes:
    """周波数スイープ（高 → 低）のホワイトノイズ混合"""
    import random
    n = int(duration * framerate)
    samples = []
    for i in range(n):
        t = i / framerate
        p = i / n  # 0→1
        freq = 1200 * (1 - p) + 200 * p  # 1200Hz→200Hz
        sine = math.sin(2 * math.pi * freq * t)
        noise = (random.random() * 2 - 1) * 0.3
        env = math.sin(math.pi * p) * (1 - p * 0.5)  # 山形エンベロープ
        samples.append((sine * 0.6 + noise) * env * 0.8)
    return _samples_to_bytes(samples)


def _synthesize_impact(duration: float = 0.4, framerate: int = 44100) -> bytes:
    """ローエンド打撃音（急速減衰）"""
    import random
    n = int(duration * framerate)
    samples = []
    for i in range(n):
        t = i / framerate
        env = math.exp(-t * 18)
        freq = 80 + 40 * math.exp(-t * 30)
        body = math.sin(2 * math.pi * freq * t)
        thud = math.sin(2 * math.pi * 40 * t)
        noise = (random.random() * 2 - 1) * 0.2
        samples.append((body * 0.5 + thud * 0.4 + noise) * env)
    return _samples_to_bytes(samples)


def _synthesize_transition(duration: float = 0.5, framerate: int = 44100) -> bytes:
    """上昇スイープ（低 → 高）"""
    n = int(duration * framerate)
    samples = []
    for i in range(n):
        t = i / framerate
        p = i / n
        freq = 300 + 1000 * p
        env = math.sin(math.pi * p) * 0.9
        samples.append(math.sin(2 * math.pi * freq * t) * env)
    return _samples_to_bytes(samples)


def _synthesize_pop(duration: float = 0.15, framerate: int = 44100) -> bytes:
    """短い高音クリック"""
    n = int(duration * framerate)
    samples = []
    for i in range(n):
        t = i / framerate
        env = math.exp(-t * 40)
        samples.append(math.sin(2 * math.pi * 1000 * t) * env * 0.9)
    return _samples_to_bytes(samples)


def _synthesize_cut(duration: float = 0.1, framerate: int = 44100) -> bytes:
    """超短音（カット点マーカー）"""
    import random
    n = int(duration * framerate)
    samples = []
    for i in range(n):
        env = math.exp(-i / n * 8)
        samples.append((random.random() * 2 - 1) * env * 0.7)
    return _samples_to_bytes(samples)


SFX_SYNTH = {
    "whoosh":     _synthesize_whoosh,
    "impact":     _synthesize_impact,
    "transition": _synthesize_transition,
    "pop":        _synthesize_pop,
    "cut":        _synthesize_cut,
}


def synthesize_sfx(sfx_types: list[str], output_dir: Path) -> dict[str, Path]:
    """SFX をローカル合成する（認証不要、完全オフライン）"""
    sfx_dir = output_dir / "sfx"
    sfx_dir.mkdir(exist_ok=True)
    result: dict[str, Path] = {}
    for sfx_type in sfx_types:
        fn = SFX_SYNTH.get(sfx_type)
        if not fn:
            print(f"  [{sfx_type}] 未対応タイプ、スキップ")
            continue
        dest = sfx_dir / f"{sfx_type}.wav"
        data = fn()
        _write_wav(dest, data)
        print(f"  [{sfx_type}] 合成完了 → {dest.name}")
        result[sfx_type] = dest
    return result


# ─── SFX 取得（キュレーションリスト + オプション Freesound API） ──────────────

def fetch_sfx_from_catalog(sfx_types: list[str], output_dir: Path) -> dict[str, Path]:
    """キュレーションリストから SFX をダウンロードする（認証不要）"""
    catalog = json.loads(SFX_CATALOG.read_text(encoding="utf-8"))
    sfx_dir = output_dir / "sfx"
    sfx_dir.mkdir(exist_ok=True)

    downloaded: dict[str, Path] = {}
    for sfx_type in sfx_types:
        entries = catalog.get(sfx_type, [])
        if not entries:
            print(f"  [{sfx_type}] カタログに未登録")
            continue
        entry = entries[0]  # 最初のバリアントを使用
        dest_ext = Path(urllib.parse.urlparse(entry["url"]).path).suffix or ".wav"
        dest = sfx_dir / f"{sfx_type}{dest_ext}"
        print(f"  [{sfx_type}] {entry['name']} ...", end="", flush=True)
        if http_download(entry["url"], dest):
            print(f" → {dest.name}")
            downloaded[sfx_type] = dest
        else:
            print(" 失敗")
    return downloaded


def fetch_sfx_from_freesound(sfx_types: list[str], api_key: str, output_dir: Path) -> dict[str, Path]:
    """Freesound API で動的検索してダウンロードする（APIキー必要）"""
    FREESOUND_API = "https://freesound.org/apiv2"
    sfx_dir = output_dir / "sfx"
    sfx_dir.mkdir(exist_ok=True)

    downloaded: dict[str, Path] = {}
    for sfx_type in sfx_types:
        print(f"  [{sfx_type}] Freesound 検索中...", end="", flush=True)
        try:
            params = {
                "query": sfx_type,
                "filter": "duration:[0 TO 3] license:Creative Commons 0",
                "sort": "rating_desc",
                "page_size": 5,
                "token": api_key,
            }
            data = json.loads(http_get(f"{FREESOUND_API}/search/text/", params))
            results = data.get("results", [])
            if not results:
                print(" 見つからず、キュレーションリストで代替")
                catalog = json.loads(SFX_CATALOG.read_text(encoding="utf-8"))
                entry = (catalog.get(sfx_type) or [{}])[0]
                preview_url = entry.get("preview_url") or entry.get("url")
                if preview_url:
                    dest_ext = Path(urllib.parse.urlparse(preview_url).path).suffix or ".wav"
                    dest = sfx_dir / f"{sfx_type}{dest_ext}"
                    http_download(preview_url, dest)
                    downloaded[sfx_type] = dest
                continue

            # 最初の結果のプレビューを取得
            sound = results[0]
            preview_url = sound.get("previews", {}).get("preview-hq-mp3", "")
            if preview_url:
                dest = sfx_dir / f"{sfx_type}.mp3"
                if http_download(preview_url, dest):
                    print(f" → {sound.get('name', '')} ({dest.name})")
                    downloaded[sfx_type] = dest
        except Exception as e:
            print(f" エラー: {e}")
    return downloaded


# ─── Remotion コード生成 ─────────────────────────────────────────────────────

def generate_audio_tsx(
    bgm_path: Path | None,
    sfx_map: dict[str, Path],
    interrupt_times: list[float],
    sfx_order: list[str] | None = None,
    fps: int = 30,
) -> str:
    """ViralVideo.tsx に追加する Audio コードスニペットを返す"""
    lines = []

    # BGM
    if bgm_path:
        rel = f"audio/{bgm_path.name}"
        lines.append(f"""      {{/* BGM (ループ再生) */}}
      <Sequence from={{0}} durationInFrames={{totalFrames}}>
        <Audio src={{staticFile("{rel}")}} volume={{0.25}} loop />
      </Sequence>""")

    # SFX（パターンインタラプトのタイミングに同期）
    ordered_sfx = sfx_order or list(sfx_map.keys())
    ordered_sfx = [sfx_type for sfx_type in ordered_sfx if sfx_type in sfx_map]
    if not ordered_sfx:
        ordered_sfx = list(sfx_map.keys())

    for i, t in enumerate(interrupt_times[:len(ordered_sfx)]):
        sfx_type = ordered_sfx[i % len(ordered_sfx)]
        sfx_file = sfx_map[sfx_type]
        frame = round(t * fps)
        rel = f"audio/sfx/{sfx_file.name}"
        lines.append(f"""      {{/* SFX: {sfx_type} @ {t:.1f}s */}}
      <Sequence from={{{frame}}}>
        <Audio src={{staticFile("{rel}")}} volume={{0.8}} />
      </Sequence>""")

    return "\n".join(lines)


# ─── メイン処理 ──────────────────────────────────────────────────────────────

def run(
    output_dir: Path,
    patterns_path: Path | None,
    freesound_key: str | None,
    offline: bool,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    # 要件を読み込む
    if patterns_path and patterns_path.exists():
        req = parse_patterns(patterns_path)
        print(f"viral_patterns.md から要件を読み込みました:")
        print(
            f"  BPM: {req['bpm']:.0f} / tone: {req['tone']} / "
            f"SFX: {req['sfx_types']} / interrupt: {req['interrupt_times']}"
        )
    else:
        req = {
            "bpm": 120,
            "tone": "entertainment",
            "sfx_types": ["whoosh", "impact", "transition"],
            "interrupt_times": [3.0, 21.0, 37.0],
            "total_duration_seconds": 54.0,
        }
        print("デフォルト要件を使用します (120BPM / entertainment / whoosh+impact+transition)")

    # ── BGM ──
    print("\n=== BGM 取得 ===")
    bgm_path = None if offline else fetch_bgm(req["tone"], req["bpm"], output_dir)
    if offline:
        print("  オフラインモードのため、ローカル生成 BGM を使用します")
    if not bgm_path:
        if not offline:
            print("  外部取得に失敗したため、ローカル生成 BGM にフォールバックします")
        bgm_path = synthesize_bgm(
            req["tone"],
            req["bpm"],
            req.get("total_duration_seconds", 54.0),
            output_dir,
        )
        print(f"  生成完了: {bgm_path.name}")

    # ── SFX ──
    print("\n=== SFX 取得 ===")
    if freesound_key:
        print(f"  Freesound API キーを使用します")
        sfx_map = fetch_sfx_from_freesound(req["sfx_types"], freesound_key, output_dir)
    else:
        print("  ローカル合成（オフライン・認証不要）")
        sfx_map = synthesize_sfx(req["sfx_types"], output_dir)

    # ── Remotion コードスニペット ──
    interrupt_times = req.get("interrupt_times", [3.0, 21.0, 37.0])
    preferred_sfx_order = [
        sfx_type for sfx_type in ("whoosh", "transition", "impact", "cut", "pop")
        if sfx_type in sfx_map
    ]
    tsx_snippet = generate_audio_tsx(
        bgm_path,
        sfx_map,
        interrupt_times,
        sfx_order=preferred_sfx_order,
    )

    # manifest 出力
    manifest = {
        "bgm": str(bgm_path) if bgm_path else None,
        "sfx": {k: str(v) for k, v in sfx_map.items()},
        "interrupt_times": interrupt_times,
        "sfx_order": preferred_sfx_order,
        "remotion_snippet": tsx_snippet,
    }
    manifest_path = output_dir / "audio_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 結果報告
    print("\n" + "=" * 60)
    print("取得完了")
    print("=" * 60)
    print(f"BGM : {bgm_path.name if bgm_path else '未取得'}")
    print(f"SFX : {', '.join(f'{k}={v.name}' for k, v in sfx_map.items()) or '未取得'}")
    print(f"マニフェスト: {manifest_path}")

    if tsx_snippet:
        print("\n── ViralVideo.tsx に追加するコード ────────────────")
        print(tsx_snippet)
        print("──────────────────────────────────────────────────")

    print("\n⚠ クレジット表記について:")
    if bgm_path and bgm_path.name == "bgm_generated.wav":
        print("  BGM はローカル生成です。外部クレジットは不要です。")
    else:
        print("  BGM は ccMixter の CC ライセンスです。動画概要欄にクレジットを記載してください。")
    if freesound_key:
        print("  SFX は Freesound / カタログ由来のため、利用元ライセンスを確認してください。")
    else:
        print("  SFX はローカル生成です。外部クレジットは不要です。")


def main():
    parser = argparse.ArgumentParser(description="BGM と SFX をフリー素材から取得")
    parser.add_argument("--output-dir", "-o", type=Path, required=False)
    parser.add_argument("--viral-patterns", "-p", type=Path, required=False,
                        help="viral_patterns.md のパス（省略時はプロジェクト内を自動検索）")
    parser.add_argument("--freesound-key", type=str,
                        default=os.environ.get("FREESOUND_API_KEY"),
                        help="Freesound API キー（省略時はキュレーションリストを使用）")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="外部アクセスを行わず、ローカル生成だけで BGM/SFX を用意する",
    )
    args = parser.parse_args()

    # output-dir の決定
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # my-video/public/viral/ 以下を優先して探す
        my_video_viral = PROJECT_ROOT / "Remotion" / "my-video" / "public" / "viral"
        if my_video_viral.exists():
            titles = [d for d in my_video_viral.iterdir() if d.is_dir()]
            if titles:
                output_dir = sorted(titles, key=lambda d: d.stat().st_mtime, reverse=True)[0] / "audio"
                print(f"出力先（自動検出）: {output_dir}")
            else:
                output_dir = my_video_viral / "unnamed" / "audio"
        else:
            output_dir = PROJECT_ROOT / "Remotion" / "my-video" / "public" / "viral" / "unnamed" / "audio"
            print(f"出力先: {output_dir}")

    # viral_patterns.md の決定
    if args.viral_patterns:
        patterns_path = args.viral_patterns
    else:
        candidates = list(PROJECT_ROOT.rglob("viral_patterns.md"))
        patterns_path = candidates[0] if candidates else None

    run(output_dir, patterns_path, args.freesound_key, args.offline)


if __name__ == "__main__":
    main()
