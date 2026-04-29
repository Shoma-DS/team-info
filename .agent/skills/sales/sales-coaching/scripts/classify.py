import json
import re

# キーワードベースの簡易分類（APIコストゼロ）
# 判別が難しいケースはCodexが目視で確認する

_1S_KEYWORDS = [
    "初めまして", "お仕事のご紹介", "お仕事紹介", "ご興味ありますか",
    "少しお時間", "こちらからご連絡", "求人を拝見", "応募いただく前に",
    "どんなお仕事か", "簡単にご説明",
]

_INTERVIEW_KEYWORDS = [
    "本日はお時間", "ありがとうございます", "経歴を教えて", "履歴書",
    "採用", "勤務開始", "いつから働け", "シフト", "面接",
    "今日はよろしく", "改めて仕事内容", "応募の動機", "面談担当",
]

_SEMINAR_KEYWORDS = [
    "セミナー", "説明会", "登壇", "参加者", "講演", "ウェビナー",
]

_REMOTE_WORK_KEYWORDS = [
    "在宅ワーク", "在宅", "リモート", "副業", "クラウドワークス", "LinkedIn",
]

_FACTORY_WORK_KEYWORDS = [
    "工場", "製造", "寮", "ライン", "夜勤", "住み込み",
]

_SCREENING_KEYWORDS = [
    "お人柄を見る会", "スクリーニング", "面談担当", "応募の動機",
    "二次面接の方", "本面接がある", "次の代表",
]

_SECOND_ROUND_KEYWORDS = [
    "二次面接", "2次面接", "二回目", "2回目", "本面接",
]

_FOLLOWUP_INTERVIEW_KEYWORDS = [
    "前回", "この前", "契約書", "秘密保持契約書", "初回レクチャー",
    "運営費", "5万円", "1万円", "次回やりましょう", "画面共有",
]

_KNOWN_FACILITATORS = {
    "deguchi": {
        "display_name": "出口",
        "aliases": ["出口正馬", "出口翔真", "出口"],
    },
    "sugashita": {
        "display_name": "菅下",
        "aliases": ["菅下政文", "菅下"],
    },
    "muto_yuna": {
        "display_name": "武藤夢奈",
        "aliases": ["武藤夢奈", "武藤"],
    },
}


def classify_type(transcript: str) -> dict:
    score_1s = sum(1 for kw in _1S_KEYWORDS if kw in transcript)
    score_iv = sum(1 for kw in _INTERVIEW_KEYWORDS if kw in transcript)

    if score_1s == 0 and score_iv == 0:
        return {"type": "unknown", "confidence": 0, "reason": "キーワード不一致。Codexが目視確認してください"}

    total = score_1s + score_iv
    if score_1s >= score_iv:
        confidence = min(100, int(score_1s / total * 100))
        return {"type": "1s", "confidence": confidence, "reason": f"1Sキーワード{score_1s}件 vs 面接キーワード{score_iv}件"}

    confidence = min(100, int(score_iv / total * 100))
    return {"type": "interview", "confidence": confidence, "reason": f"面接キーワード{score_iv}件 vs 1Sキーワード{score_1s}件"}


def classify_speaker(transcript: str) -> dict:
    intro_window = transcript[:5000]
    candidates = []

    for slug, meta in _KNOWN_FACILITATORS.items():
        best = None
        for alias in meta["aliases"]:
            idx = intro_window.find(alias)
            if idx == -1:
                continue
            context = intro_window[max(0, idx - 30): idx + len(alias) + 40]
            score = 40
            if idx < 1200:
                score += 20
            if re.search(r"(面談担当|担当|申します|よろしく|ご参加)", context):
                score += 30
            if re.search(r"(代表|社長)", context):
                score -= 20
            candidate = {
                "speaker": slug,
                "display_name": meta["display_name"],
                "confidence": min(100, score),
                "style_notes": [],
                "reason": f"冒頭の自己紹介付近で「{alias}」を検出",
                "organization_name": extract_organization_name(transcript),
                "role": infer_facilitator_role(context),
            }
            if best is None or candidate["confidence"] > best["confidence"]:
                best = candidate
        if best is not None:
            candidates.append(best)

    if candidates:
        candidates.sort(key=lambda item: item["confidence"], reverse=True)
        best = candidates[0]
        if len(candidates) == 1 or best["confidence"] >= candidates[1]["confidence"] + 15:
            return best

    fallback = infer_facilitator_from_addressing(transcript)
    if fallback:
        return fallback

    return {
        "speaker": "unknown",
        "display_name": "unknown",
        "confidence": 0,
        "style_notes": [],
        "reason": "自己紹介から担当者名を特定できませんでした。Codexが目視確認してください",
        "organization_name": extract_organization_name(transcript),
        "role": "unknown",
    }


def classify_session_context(transcript: str, video_name: str = "") -> dict:
    title = video_name or ""
    combined = f"{title}\n{transcript}"
    intro_window = transcript[:5000]
    has_interview_title = any(token in title for token in ("面談", "面接", "予約"))

    seminar_hits = _count_hits(combined, _SEMINAR_KEYWORDS)
    remote_hits = _count_hits(combined, _REMOTE_WORK_KEYWORDS)
    factory_hits = _count_hits(combined, _FACTORY_WORK_KEYWORDS)
    screening_hits = _count_hits(intro_window, _SCREENING_KEYWORDS)
    second_hits_title = _count_hits(title, _SECOND_ROUND_KEYWORDS)
    second_hits_intro = _count_hits(intro_window, _SECOND_ROUND_KEYWORDS)
    followup_hits = _count_hits(combined, _FOLLOWUP_INTERVIEW_KEYWORDS)

    base_type = classify_type(transcript)
    session_kind = "other"
    reason_parts = []

    if has_interview_title and base_type["type"] == "interview" and followup_hits >= 3 and screening_hits == 0:
        session_kind = "followup_interview"
        reason_parts.append(f"{base_type['reason']} / フォローアップ系キーワード{followup_hits}件")
    elif seminar_hits >= 2 and not has_interview_title and base_type["confidence"] < 70:
        session_kind = "seminar"
        reason_parts.append(f"セミナー系キーワード{seminar_hits}件")
    elif base_type["type"] == "1s":
        session_kind = "1s"
        reason_parts.append(base_type["reason"])
    elif second_hits_title > 0 or (second_hits_intro > 0 and "本面接" in title):
        session_kind = "second_interview"
        reason_parts.append(f"2回目系キーワード{second_hits_title + second_hits_intro}件")
    elif base_type["type"] == "interview" and screening_hits > 0:
        session_kind = "initial_interview"
        reason_parts.append(f"{base_type['reason']} / スクリーニング系キーワード{screening_hits}件")
    elif base_type["type"] == "interview":
        session_kind = "interview"
        reason_parts.append(base_type["reason"])

    work_domain = "other"
    if remote_hits > 0:
        work_domain = "remote_work"
        reason_parts.append(f"在宅ワーク系キーワード{remote_hits}件")
    elif factory_hits > 0:
        work_domain = "factory_work"
        reason_parts.append(f"工場系キーワード{factory_hits}件")

    tags = []
    if session_kind == "seminar":
        tags.extend(["seminar", "education"])
    elif session_kind == "1s":
        tags.extend(["1s", "initial_contact"])
    elif session_kind == "initial_interview":
        tags.extend(["interview", "screening"])
    elif session_kind == "followup_interview":
        tags.extend(["interview", "followup"])
    elif session_kind == "second_interview":
        tags.extend(["interview", "second_round"])
    elif session_kind == "interview":
        tags.append("interview")

    if work_domain == "remote_work":
        tags.append("remote_work")
    elif work_domain == "factory_work":
        tags.append("factory_work")

    confidence = _session_confidence(session_kind, seminar_hits, screening_hits, second_hits_title, base_type["confidence"])
    return {
        "session_kind": session_kind,
        "work_domain": work_domain,
        "tags": _unique(tags),
        "confidence": confidence,
        "reason": " / ".join(part for part in reason_parts if part) or "キーワード不足",
    }


def metadata_summary_json(facilitator: dict, session: dict) -> str:
    payload = {
        "facilitator_name": facilitator.get("display_name"),
        "facilitator_slug": facilitator.get("speaker"),
        "facilitator_role": facilitator.get("role"),
        "organization_name": facilitator.get("organization_name"),
        "session_kind": session.get("session_kind"),
        "work_domain": session.get("work_domain"),
        "session_tags": session.get("tags", []),
    }
    return json.dumps(payload, ensure_ascii=False)


def extract_organization_name(transcript: str) -> str:
    intro_window = transcript[:3000]
    patterns = [
        r"私(?P<org>株式会社[^\s、。\]]{1,30}?)(?=の|と申します|です|、|。)",
        r"\[(?P<org>株式会社[^\]]{1,30})\]",
    ]
    for pattern in patterns:
        match = re.search(pattern, intro_window)
        if match:
            return match.group("org")
    return ""


def infer_facilitator_role(text: str) -> str:
    if "面談担当" in text:
        return "面談担当"
    if "担当" in text:
        return "担当"
    if "代表" in text or "社長" in text:
        return "代表"
    return "unknown"


def _count_hits(text: str, keywords: list[str]) -> int:
    return sum(1 for kw in keywords if kw in text)


def _session_confidence(
    session_kind: str,
    seminar_hits: int,
    screening_hits: int,
    second_hits_title: int,
    base_confidence: int,
) -> int:
    if session_kind == "seminar":
        return min(100, 70 + seminar_hits * 5)
    if session_kind == "followup_interview":
        return min(100, max(base_confidence, 72 + screening_hits * 2))
    if session_kind == "second_interview":
        return min(100, 70 + second_hits_title * 10)
    if session_kind == "initial_interview":
        return min(100, max(base_confidence, 75 + screening_hits * 3))
    if session_kind in {"interview", "1s"}:
        return base_confidence
    return max(30, base_confidence)


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def infer_facilitator_from_addressing(transcript: str) -> dict | None:
    clues = []
    speaker_lines = []
    for line in transcript.splitlines():
        if "] " in line:
            _, _, body = line.partition("] ")
            speaker_lines.append(body)
    body_text = "\n".join(speaker_lines)

    if body_text.count("出口さん") >= 2 and "菅下" not in body_text and "武藤" not in body_text:
        clues.append(("deguchi", "出口", body_text.count("出口さん"), "相手側の呼びかけで「出口さん」を複数検出"))
    if body_text.count("菅下さん") >= 2 and "出口" not in body_text and "武藤" not in body_text:
        clues.append(("sugashita", "菅下", body_text.count("菅下さん"), "相手側の呼びかけで「菅下さん」を複数検出"))
    if body_text.count("武藤さん") >= 2 and "出口" not in body_text and "菅下" not in body_text:
        clues.append(("muto_yuna", "武藤夢奈", body_text.count("武藤さん"), "相手側の呼びかけで「武藤さん」を複数検出"))

    if not clues:
        return None

    slug, display_name, hits, reason = sorted(clues, key=lambda item: item[2], reverse=True)[0]
    return {
        "speaker": slug,
        "display_name": display_name,
        "confidence": min(75, 45 + hits * 5),
        "style_notes": [],
        "reason": reason,
        "organization_name": extract_organization_name(transcript),
        "role": "担当",
    }
