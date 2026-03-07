"""
Layer 3: バズ構造解析
- フック検出（最初の3秒）
- パターンインタラプト検出（急速なカット変化）
- ループ構造検出（終端→先頭の類似度）
- 情報密度計算（テロップ量 + カット速度）
"""
from __future__ import annotations
import math


# ─── フック検出 ───────────────────────────────────────────────────────────────

def detect_hook(video_data: dict, speech_data: dict) -> tuple[float, str]:
    """
    最初の3秒を解析してフックタイプを判定する。
    Returns: (hook_time, hook_type)
      hook_type: "question" | "statement" | "visual" | "unknown"
    """
    hook_time = 0.0

    # 最初の発話を確認
    transcript = speech_data.get("transcript", [])
    first_seg = transcript[0] if transcript else None

    if first_seg and first_seg["start"] < 3.0:
        text = first_seg["text"]
        if "?" in text or "？" in text or text.endswith("か") or text.endswith("の"):
            return (first_seg["start"], "question")
        if any(kw in text for kw in ["実は", "知らない", "秘密", "衝撃", "絶対", "やばい"]):
            return (first_seg["start"], "statement")
        return (first_seg["start"], "statement")

    # 音声なし → 視覚フック
    cuts = video_data.get("video_structure", {}).get("cuts", [])
    if cuts and cuts[0]["end"] - cuts[0]["start"] < 1.5:
        return (0.0, "visual")

    return (hook_time, "unknown")


# ─── パターンインタラプト ──────────────────────────────────────────────────────

def detect_pattern_interrupts(video_data: dict, speech_data: dict) -> list[float]:
    """
    急速なカット + ポーズの組み合わせからパターンインタラプトの時刻を検出する。
    """
    interrupts: list[float] = []
    cuts = video_data.get("video_structure", {}).get("cuts", [])
    pauses = speech_data.get("pauses", [])

    # カット間隔が短い（1秒未満）連続箇所
    for i in range(len(cuts) - 1):
        dur = cuts[i]["end"] - cuts[i]["start"]
        if dur < 1.0 and cuts[i]["start"] > 1.0:
            interrupts.append(cuts[i]["start"])

    # 音声ポーズ直後のカット
    pause_times = {round(p["end"], 1) for p in pauses if p["duration"] > 0.3}
    for cut in cuts:
        if round(cut["start"], 1) in pause_times:
            t = cut["start"]
            if t not in interrupts:
                interrupts.append(t)

    return sorted(set(round(t, 3) for t in interrupts))


# ─── ループ構造検出 ───────────────────────────────────────────────────────────

def detect_loop_point(video_data: dict, speech_data: dict) -> float | None:
    """
    終端→先頭に戻れるループ構造の起点時刻を推定する。
    ・最終カットが短い（2秒未満）→ ループ候補
    ・最後の発話が疑問形 → ループ候補
    """
    duration = video_data.get("duration", 0)
    cuts = video_data.get("video_structure", {}).get("cuts", [])

    if cuts:
        last_cut = cuts[-1]
        last_dur = last_cut["end"] - last_cut["start"]
        if last_dur < 2.0:
            return round(last_cut["start"], 3)

    transcript = speech_data.get("transcript", [])
    if transcript:
        last_text = transcript[-1]["text"]
        if last_text.endswith("か") or last_text.endswith("？") or last_text.endswith("?"):
            return round(transcript[-1]["start"], 3)

    # fallback: 動画の90%地点
    return round(duration * 0.9, 3) if duration > 0 else None


# ─── 情報密度 ─────────────────────────────────────────────────────────────────

def calc_information_density(video_data: dict, speech_data: dict) -> str:
    """
    カット速度 + テロップ数 + WPM から情報密度を 3段階で評価する。
    """
    duration = max(video_data.get("duration", 1), 1)
    cuts = video_data.get("video_structure", {}).get("cuts", [])
    text_regions = video_data.get("video_structure", {}).get("text_regions", [])
    wpm = speech_data.get("words_per_minute", 0)

    cuts_per_sec = len(cuts) / duration
    texts_per_sec = len(text_regions) / duration

    score = 0
    if cuts_per_sec > 1.0:
        score += 2
    elif cuts_per_sec > 0.5:
        score += 1

    if texts_per_sec > 0.5:
        score += 2
    elif texts_per_sec > 0.2:
        score += 1

    if wpm > 300:
        score += 2
    elif wpm > 180:
        score += 1

    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


# ─── 動画トーン推定 ───────────────────────────────────────────────────────────

def estimate_tone(speech_data: dict, viral_data: dict) -> str:
    """キーワードとパターンから動画のトーンを推定"""
    keywords = speech_data.get("keywords", [])
    hook_type = viral_data.get("hook_type", "")
    emotional = speech_data.get("emotional_intensity", "low")

    educational_kw = {"方法", "やり方", "コツ", "解説", "理由", "仕組み"}
    entertainment_kw = {"面白い", "爆笑", "やばい", "すごい", "びっくり"}

    kw_set = set(keywords)
    if kw_set & educational_kw:
        return "educational"
    if kw_set & entertainment_kw or emotional == "high":
        return "entertainment"
    if hook_type == "question":
        return "curiosity"
    return "general"


# ─── メイン ───────────────────────────────────────────────────────────────────

def analyze_viral_pattern(video_data: dict, speech_data: dict) -> dict:
    """Layer 3 エントリポイント"""
    hook_time, hook_type = detect_hook(video_data, speech_data)
    pattern_interrupts = detect_pattern_interrupts(video_data, speech_data)
    loop_point = detect_loop_point(video_data, speech_data)
    information_density = calc_information_density(video_data, speech_data)

    viral_data = {
        "hook_time": hook_time,
        "hook_type": hook_type,
        "pattern_interrupts": pattern_interrupts,
        "loop_point": loop_point,
        "information_density": information_density,
    }

    viral_data["tone"] = estimate_tone(speech_data, viral_data)
    return viral_data
