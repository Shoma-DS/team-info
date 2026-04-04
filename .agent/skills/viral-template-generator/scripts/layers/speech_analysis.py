"""
Layer 2: 音声解析
- ffmpeg で音声抽出
- faster-whisper で書き起こし
- 話速 (WPM) 計算
- キーワード抽出
- 感情強度推定（発話スピード・ポーズ頻度から）
"""
from __future__ import annotations
import json
import re
import subprocess
import tempfile
import wave
from collections import Counter
from pathlib import Path


# ─── 音声抽出 ─────────────────────────────────────────────────────────────────

def extract_audio(video_path: Path, output_dir: Path) -> Path:
    """ffmpeg で動画から 16kHz mono WAV を抽出"""
    audio_path = output_dir / "audio.wav"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-ar", "16000", "-ac", "1", "-f", "wav", str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 音声抽出に失敗しました:\n{result.stderr}")
    return audio_path


# ─── Whisper 書き起こし ───────────────────────────────────────────────────────

_faster_whisper_model = None  # プロセス内で1回だけロードして使い回す


def transcribe_with_faster_whisper(audio_path: Path) -> list[dict]:
    """faster-whisper で書き起こし（セグメント単位）"""
    try:
        from faster_whisper import WhisperModel
        global _faster_whisper_model
        if _faster_whisper_model is None:
            _faster_whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
        model = _faster_whisper_model
        segments, _ = model.transcribe(str(audio_path), language="ja", word_timestamps=True)
        # 音声の総時間を取得して進捗バーに使う
        try:
            with wave.open(str(audio_path), "rb") as wf:
                total_seconds = wf.getnframes() / wf.getframerate()
        except Exception:
            total_seconds = 0.0
        from tqdm import tqdm
        transcript = []
        with tqdm(total=int(total_seconds), unit="s", desc="    書き起こし", leave=False, ncols=60) as pbar:
            prev_end = 0.0
            for seg in segments:
                entry = {
                    "start": round(seg.start, 3),
                    "end": round(seg.end, 3),
                    "text": seg.text.strip(),
                }
                if hasattr(seg, "words") and seg.words:
                    entry["words"] = [
                        {"word": w.word, "start": round(w.start, 3), "end": round(w.end, 3)}
                        for w in seg.words
                    ]
                transcript.append(entry)
                advance = int(seg.end) - int(prev_end)
                if advance > 0:
                    pbar.update(advance)
                prev_end = seg.end
        return transcript
    except ImportError:
        pass

    # fallback: openai-whisper
    try:
        import whisper
        model = whisper.load_model("small")
        result = model.transcribe(str(audio_path), language="ja", word_timestamps=True)
        transcript = []
        for seg in result["segments"]:
            transcript.append({
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "text": seg["text"].strip(),
            })
        return transcript
    except ImportError:
        raise RuntimeError(
            "faster-whisper または openai-whisper のどちらかをインストールしてください:\n"
            "  team_info_runtime.py build-remotion-python"
        )


# ─── 指標計算 ─────────────────────────────────────────────────────────────────

def calc_words_per_minute(transcript: list[dict]) -> float:
    """発話時間あたりの文字数からおおよその WPM を計算（日本語は文字/分）"""
    total_chars = sum(len(seg["text"]) for seg in transcript)
    total_speech_time = sum(
        seg["end"] - seg["start"] for seg in transcript if seg["end"] > seg["start"]
    )
    if total_speech_time <= 0:
        return 0.0
    return round(total_chars / total_speech_time * 60, 1)


def extract_keywords(transcript: list[dict], top_n: int = 10) -> list[str]:
    """単語頻度ベースのキーワード抽出（簡易版）"""
    text = " ".join(seg["text"] for seg in transcript)
    # 2文字以上の語を抽出（ストップワード除外は簡略化）
    stop_words = {"です", "ます", "ので", "けど", "から", "って", "ある", "いる",
                  "する", "この", "その", "あの", "という", "ため", "こと", "もの"}
    words = [w for w in re.findall(r"[一-龯ぁ-んァ-ンa-zA-Z]{2,}", text) if w not in stop_words]
    counter = Counter(words)
    return [w for w, _ in counter.most_common(top_n)]


def estimate_emotional_intensity(transcript: list[dict], wpm: float) -> str:
    """発話速度とポーズ頻度から感情強度を推定"""
    if wpm > 300:
        return "high"
    if wpm > 180:
        return "medium"
    return "low"


def detect_pauses(transcript: list[dict], threshold: float = 0.5) -> list[dict]:
    """発話間のポーズを検出"""
    pauses: list[dict] = []
    for i in range(len(transcript) - 1):
        gap = transcript[i + 1]["start"] - transcript[i]["end"]
        if gap >= threshold:
            pauses.append({
                "start": round(transcript[i]["end"], 3),
                "end": round(transcript[i + 1]["start"], 3),
                "duration": round(gap, 3),
            })
    return pauses


# ─── メイン ───────────────────────────────────────────────────────────────────

def analyze_speech(video_path: Path, output_dir: Path) -> dict:
    """Layer 2 エントリポイント"""
    print("    音声抽出中 (ffmpeg)...")
    audio_path = extract_audio(video_path, output_dir)

    print("    Whisper 書き起こし中...")
    transcript = transcribe_with_faster_whisper(audio_path)

    wpm = calc_words_per_minute(transcript)
    keywords = extract_keywords(transcript)
    emotional_intensity = estimate_emotional_intensity(transcript, wpm)
    pauses = detect_pauses(transcript)

    # 全文テキスト
    full_text = " ".join(seg["text"] for seg in transcript)

    return {
        "transcript": transcript,
        "full_text": full_text,
        "words_per_minute": wpm,
        "keywords": keywords,
        "emotional_intensity": emotional_intensity,
        "pauses": pauses,
    }
