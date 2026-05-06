#!/usr/bin/env python3
"""
Viral short quality verifier.
Checks audio duration, subtitle timing, subtitle card density, and simple
ViralTemplate layout assumptions before final render.
"""
import argparse
import re
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    level: str
    item: str
    detail: str


def read_audio_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def parse_subtitles(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\{\s*from:\s*(\d+),\s*to:\s*(\d+),\s*text:\s*([\"'])(.*?)\3\s*\}",
        re.DOTALL,
    )
    entries = []
    for match in pattern.finditer(text):
        raw_text = match.group(4)
        subtitle_text = raw_text.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
        entries.append(
            {
                "from": int(match.group(1)),
                "to": int(match.group(2)),
                "text": subtitle_text,
            }
        )
    return entries


def parse_tsx_metrics(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    metrics: dict = {
        "section_count": len(re.findall(r"\btitle:\s*[\"'`]", text)),
        "visual_count": len(re.findall(r"\bfromFrame:\s*\d+", text)),
        "has_viral_template": "ViralTemplate" in text,
        "subtitle_padding_bottom": None,
        "visual_top": None,
        "visual_height": None,
    }
    padding_match = re.search(r"paddingBottom:\s*isHorizontal\s*\?\s*[\"'][^\"']+[\"']\s*:\s*[\"']([^\"']+)[\"']", text)
    if padding_match:
        metrics["subtitle_padding_bottom"] = padding_match.group(1)
    top_match = re.search(r"top:\s*isHorizontal\s*\?\s*[\"'][^\"']+[\"']\s*:\s*[\"']([^\"']+)[\"']", text)
    if top_match:
        metrics["visual_top"] = top_match.group(1)
    height_match = re.search(r"height:\s*isHorizontal\s*\?\s*[\"'][^\"']+[\"']\s*:\s*[\"']([^\"']+)[\"']", text)
    if height_match:
        metrics["visual_height"] = height_match.group(1)
    return metrics


def line_lengths(text: str) -> list[int]:
    return [len(line) for line in text.split("\\n")]


def verify(
    tsx_path: Path,
    audio_path: Path,
    subtitles_path: Path,
    duration_frames: int,
    fps: int,
    scoring_path: Path,
    still_dir: Path | None,
) -> list[Finding]:
    findings: list[Finding] = []
    audio_seconds = read_audio_seconds(audio_path)
    audio_frames = round(audio_seconds * fps)
    duration_delta = duration_frames - audio_frames

    if abs(duration_delta) > fps:
        findings.append(
            Finding(
                "fail",
                "音声尺",
                f"composition={duration_frames}f / audio={audio_frames}f / delta={duration_delta}f。1秒以上ズレています。",
            )
        )
    elif abs(duration_delta) > 6:
        findings.append(
            Finding(
                "warn",
                "音声尺",
                f"composition={duration_frames}f / audio={audio_frames}f / delta={duration_delta}f。末尾余白を確認してください。",
            )
        )

    subtitles = parse_subtitles(subtitles_path)
    if not subtitles:
        findings.append(Finding("fail", "字幕", "SUBTITLE_TIMELINE を取得できませんでした。"))
    else:
        last_to = max(entry["to"] for entry in subtitles)
        if last_to > duration_frames:
            findings.append(Finding("fail", "字幕尺", f"最終字幕 {last_to}f が composition {duration_frames}f を超えています。"))
        if last_to > audio_frames + 12:
            findings.append(Finding("warn", "字幕/音声ズレ", f"最終字幕 {last_to}f が音声末尾 {audio_frames}f より 12f 以上後ろです。"))
        if last_to < audio_frames - fps:
            findings.append(Finding("warn", "字幕/音声ズレ", f"最終字幕 {last_to}f が音声末尾 {audio_frames}f より 1秒以上早く終わります。"))

        previous_visible_to = -1
        for index, entry in enumerate(subtitles, start=1):
            text = entry["text"]
            duration = entry["to"] - entry["from"]
            if not text:
                continue
            if entry["from"] < previous_visible_to:
                findings.append(Finding("fail", "字幕重複", f"#{index} {entry['from']}f が前の表示字幕終了 {previous_visible_to}f より前です。"))
            previous_visible_to = entry["to"]
            lines = line_lengths(text)
            if len(lines) > 3:
                findings.append(Finding("warn", "字幕行数", f"#{index} が {len(lines)} 行です。2-3行以内が基準です: {text}"))
            if max(lines) > 20:
                findings.append(Finding("warn", "字幕横幅", f"#{index} の最長行が {max(lines)} 文字です。文節で分割を検討: {text}"))
            if duration < 18:
                findings.append(Finding("warn", "字幕表示時間", f"#{index} が {duration}f です。短すぎて読みにくい可能性があります: {text}"))
            if duration > 150:
                findings.append(Finding("warn", "字幕表示時間", f"#{index} が {duration}f です。長すぎる可能性があります: {text}"))

    metrics = parse_tsx_metrics(tsx_path)
    if not metrics["has_viral_template"]:
        findings.append(Finding("warn", "構成", "ViralTemplate 利用を検出できませんでした。手動でレイアウト確認してください。"))
    if metrics["section_count"] < 3:
        findings.append(Finding("warn", "構成", f"section title が {metrics['section_count']} 件です。3セクション構成か確認してください。"))
    if metrics["visual_count"] < 10:
        findings.append(Finding("warn", "画像テンポ", f"fromFrame が {metrics['visual_count']} 件です。文単位の視覚変化が足りない可能性があります。"))

    scoring_text = scoring_path.read_text(encoding="utf-8") if scoring_path.exists() else ""
    if "画像と字幕は重ねない" not in scoring_text:
        findings.append(Finding("warn", "採点基準", f"採点基準ファイルを確認できません: {scoring_path}"))

    if still_dir:
        if not still_dir.exists():
            findings.append(Finding("warn", "still確認", f"still-dir が存在しません: {still_dir}"))
        else:
            stills = [p for p in still_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
            if len(stills) < 4:
                findings.append(Finding("warn", "still確認", f"代表 still が {len(stills)} 枚です。hook/section/CTA の目視確認に不足しています。"))

    return findings


def write_report(path: Path, findings: list[Finding], scoring_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Viral Short Quality Report",
        "",
        f"- 採点基準: `{scoring_path}`",
        f"- fail: {sum(1 for f in findings if f.level == 'fail')}",
        f"- warn: {sum(1 for f in findings if f.level == 'warn')}",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("- OK: 自動検証で重大な問題は見つかりませんでした。still の目視確認は別途行ってください。")
    else:
        for finding in findings:
            lines.append(f"- {finding.level.upper()} / {finding.item}: {finding.detail}")
    lines.extend(
        [
            "",
            "## Manual Still Checklist",
            "",
            "- 画像と字幕の間に 50px 以上の余白がある",
            "- 字幕が下部 UI に隠れない",
            "- 横長写真でも幅 85-92% 程度で小さすぎない",
            "- フックタイトルは最初の1秒で読める",
            "- CTA 前後の画像と字幕が重ならない",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    default_scoring = (
        Path(__file__).resolve().parents[2]
        / "remotion"
        / "video-production"
        / "remotion-short-sound-design"
        / "references"
        / "templates"
        / "viral-short-vertical.md"
    )
    parser = argparse.ArgumentParser(description="Viral short final quality checker")
    parser.add_argument("--tsx", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--subtitles", type=Path, required=True)
    parser.add_argument("--duration-frames", type=int, required=True)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--scoring", type=Path, default=default_scoring)
    parser.add_argument("--still-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    findings = verify(
        args.tsx,
        args.audio,
        args.subtitles,
        args.duration_frames,
        args.fps,
        args.scoring,
        args.still_dir,
    )
    if args.report:
        write_report(args.report, findings, args.scoring)
        print(f"report: {args.report}")

    fail_count = sum(1 for finding in findings if finding.level == "fail")
    warn_count = sum(1 for finding in findings if finding.level == "warn")
    print(f"fail={fail_count} warn={warn_count}")
    for finding in findings:
        print(f"{finding.level.upper()} {finding.item}: {finding.detail}")
    raise SystemExit(1 if fail_count else 0)


if __name__ == "__main__":
    main()
