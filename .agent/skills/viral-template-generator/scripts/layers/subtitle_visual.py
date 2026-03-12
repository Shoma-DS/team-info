"""
Layer 4: 字幕ビジュアルスタイル解析

OpenCV でテキスト領域を画素レベルで分析し、以下を検出する:
  - font_size_px          : フォントサイズ推定 (px @ 1920h)
  - font_size_relative    : フォント高さ / 動画高さ
  - text_color_hex        : 文字色 (例 "#ffffff")
  - multicolor_lines      : 行ごとに色が変わるか
  - line_colors_hex       : 行ごとの推定色リスト
  - stroke_detected       : 縁取りの有無
  - stroke_width_px       : 縁取り幅推定 (px @ 動画解像度)
  - stroke_color_hex      : 縁取り色
  - glow_detected         : グロー効果の有無
  - glow_color_hex        : グロー色
  - background_box_detected   : 座布団（背景ハイライトボックス）の有無
  - background_box_color_hex  : 座布団の色
  - background_box_opacity    : 座布団の推定不透明度 (0.0–1.0)
"""
from __future__ import annotations

import cv2
import numpy as np
import json
from pathlib import Path

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    def tqdm(it, **kw):  # type: ignore[misc]
        return it


# ──────────────────────────────────────────────────────────────────────────────
# ユーティリティ
# ──────────────────────────────────────────────────────────────────────────────

def _bgr_to_hex(bgr: tuple[int, int, int]) -> str:
    b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
    return f"#{r:02x}{g:02x}{b:02x}"


def _dominant_color(pixels: np.ndarray, k: int = 3) -> np.ndarray:
    """ピクセル群の中の支配色を k-means で返す (BGR)。"""
    if len(pixels) == 0:
        return np.array([0, 0, 0], dtype=np.uint8)
    data = pixels.reshape(-1, 3).astype(np.float32)
    if len(data) < k:
        return data[0].astype(np.uint8)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(
        data, k, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS
    )
    counts = np.bincount(labels.flatten())
    return centers[counts.argmax()].astype(np.uint8)


def _luminance(bgr: np.ndarray) -> np.ndarray:
    """BGR 配列のピクセルごとに輝度 (0–255) を返す。"""
    return (0.114 * bgr[..., 0] + 0.587 * bgr[..., 1] + 0.299 * bgr[..., 2]).astype(np.uint8)


def _normalize_bbox_value(value: float | int, full_size: int) -> int:
    if value <= 1.0:
        return int(round(float(value) * full_size))
    return int(round(float(value)))


def _region_to_bbox(
    region: dict,
    video_width: int,
    video_height: int,
) -> tuple[int, int, int, int]:
    text = str(region.get("text", "")).strip()
    fallback_w = min(video_width, max(120, int(len(text) * video_height * 0.02)))
    fallback_h = max(40, int(video_height * 0.035))

    width = _normalize_bbox_value(region.get("width", fallback_w), video_width) if "width" in region else fallback_w
    height = _normalize_bbox_value(region.get("height", fallback_h), video_height) if "height" in region else fallback_h
    width = max(40, width)
    height = max(24, height)

    if "left" in region and "top" in region:
        left = _normalize_bbox_value(region.get("left", 0), video_width)
        top = _normalize_bbox_value(region.get("top", 0), video_height)
    else:
        x_center = _normalize_bbox_value(region.get("x", 0), video_width)
        y_center = _normalize_bbox_value(region.get("y", 0), video_height)
        left = x_center - width // 2
        top = y_center - height // 2

    left = max(0, min(video_width - 1, left))
    top = max(0, min(video_height - 1, top))
    width = min(width, video_width - left)
    height = min(height, video_height - top)
    return left, top, width, height


def _combine_regions_bbox(
    regions: list[dict],
    video_width: int,
    video_height: int,
) -> tuple[int, int, int, int]:
    boxes = [_region_to_bbox(region, video_width, video_height) for region in regions]
    x1 = min(box[0] for box in boxes)
    y1 = min(box[1] for box in boxes)
    x2 = max(box[0] + box[2] for box in boxes)
    y2 = max(box[1] + box[3] for box in boxes)
    return x1, y1, max(1, x2 - x1), max(1, y2 - y1)


def _quantize_hex_color(hex_color: str | None, step: int = 32) -> str:
    if not hex_color:
        return "none"
    raw = hex_color.lstrip("#")
    if len(raw) != 6:
        return hex_color
    channels = []
    for idx in range(0, 6, 2):
        value = int(raw[idx:idx + 2], 16)
        quantized = min(255, int(round(value / step) * step))
        channels.append(f"{quantized:02x}")
    return "#" + "".join(channels)


def _subtitle_zone_label(y_percent: float) -> str:
    if y_percent < 35:
        return "top"
    if y_percent < 65:
        return "middle"
    return "bottom"


def _build_style_signature(
    feature: dict,
    bbox: tuple[int, int, int, int],
    video_height: int,
) -> str:
    _, y1, _, h1 = bbox
    y_percent = ((y1 + h1 / 2) / max(video_height, 1)) * 100
    stroke_width = int(round(feature.get("stroke_width_px", 0) or 0))
    stroke_bucket = "0" if stroke_width <= 0 else "2" if stroke_width <= 2 else "4"
    parts = [
        f"zone:{_subtitle_zone_label(y_percent)}",
        f"bg:{int(bool(feature.get('background_box_detected')))}",
        f"stroke:{int(bool(feature.get('stroke_detected')))}:{stroke_bucket}",
        f"multi:{int(bool(feature.get('multicolor_lines')))}",
        f"text:{_quantize_hex_color(feature.get('text_color_hex'))}",
        f"box:{_quantize_hex_color(feature.get('background_box_color_hex'))}",
    ]
    return "|".join(parts)


def _write_review_template(
    template_path: Path,
    manifest_path: Path,
    source_video: str | None,
    samples: list[dict],
) -> None:
    template = {
        "status": "pending_agent_review",
        "mode": "agent_review_preferred",
        "source_video": source_video,
        "manifest_path": str(manifest_path),
        "reviewed_sample_ids": [sample["id"] for sample in samples],
        "subtitle": {
            "template_name": None,
            "fontFamily": None,
            "fontWeight": None,
            "fontSizePx1920h": None,
            "letterSpacing": None,
            "lineHeight": None,
            "textColor": None,
            "lineColors": [],
            "strokeWidthPx": None,
            "strokeColor": None,
            "textShadow": None,
            "background": None,
            "paddingH": None,
            "paddingV": None,
            "borderRadius": None,
            "yPercent": None,
            "alignment": "center",
            "notes": None,
        },
        "hook": {
            "fontFamily": None,
            "fontWeight": None,
            "fontSizePx1920h": None,
            "lineColors": [],
            "strokeWidthPx": None,
            "strokeColor": None,
            "textShadow": None,
            "notes": None,
        },
    }
    template_path.write_text(
        json.dumps(template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_review_readme(
    readme_path: Path,
    template_path: Path,
    samples: list[dict],
) -> None:
    lines = [
        "# Subtitle Style Review",
        "",
        "AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。",
        f"レビュー結果は `{template_path.name}` に保存する。",
        "",
        "## Samples",
        "",
    ]
    for sample in samples:
        lines.extend([
            f"### {sample['id']}",
            f"- cut: {sample['cut_range']}",
            f"- frame: {sample['frame']} ({sample['time_seconds']}s)",
            f"- text_preview: {sample['text_preview']}",
            f"- full_frame_path: {sample['full_frame_path']}",
            f"- subtitle_crop_path: {sample['subtitle_crop_path']}",
            f"- heuristic_signature: {sample['style_signature']}",
            "",
        ])
    readme_path.write_text("\n".join(lines), encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# 1. フォントサイズ推定
# ──────────────────────────────────────────────────────────────────────────────

def _estimate_font_size(
    text_regions: list[dict],
    video_height: int,
    video_width: int,
) -> dict:
    """text_regions のバウンディングボックス高さからフォントサイズを推定する。"""
    if not text_regions:
        return {"font_size_px": 0, "font_size_relative": 0.0}

    heights = [
        int(r.get("height", 0) * video_height)
        if r.get("height", 0) <= 1.0
        else int(r.get("height", 0))
        for r in text_regions
    ]
    # ゼロや外れ値を除く
    heights = [h for h in heights if 5 < h < video_height * 0.3]
    if not heights:
        return {"font_size_px": 0, "font_size_relative": 0.0}

    median_h = float(np.median(heights))
    return {
        "font_size_px": round(median_h),
        "font_size_relative": round(median_h / video_height, 4),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 2. テキスト色・縁取り・グロー・座布団の検出（フレーム単位）
# ──────────────────────────────────────────────────────────────────────────────

def _analyze_frame_region(
    frame: np.ndarray,
    rx: int, ry: int, rw: int, rh: int,
    pad: int = 6,
) -> dict:
    """
    1枚のフレームとテキスト領域 (rx,ry,rw,rh) から視覚特徴を抽出する。
    pad: 縁取り・グロー検出用の周辺ピクセル余白。
    """
    h, w = frame.shape[:2]

    # ── ROI クリッピング ──────────────────────────────────────────────────
    x1 = max(0, rx - pad)
    y1 = max(0, ry - pad)
    x2 = min(w, rx + rw + pad)
    y2 = min(h, ry + rh + pad)
    if x2 <= x1 or y2 <= y1:
        return {}

    roi = frame[y1:y2, x1:x2]
    inner_x1 = rx - x1
    inner_y1 = ry - y1
    inner_x2 = inner_x1 + rw
    inner_y2 = inner_y1 + rh

    # ── テキストマスク（高輝度ピクセル） ─────────────────────────────────
    lum = _luminance(roi)
    # Otsu でテキスト/背景を分離
    _, text_mask = cv2.threshold(lum, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # テキスト領域内のみ対象
    inner_mask = np.zeros_like(text_mask)
    inner_mask[inner_y1:inner_y2, inner_x1:inner_x2] = 255
    text_pixels_mask = cv2.bitwise_and(text_mask, inner_mask)

    # テキスト色（明るいピクセルの支配色）
    text_px = roi[text_pixels_mask > 0]
    text_color = _dominant_color(text_px, k=2) if len(text_px) > 0 else np.array([255, 255, 255])

    # ── 縁取り検出 ─────────────────────────────────────────────────────────
    stroke_detected = False
    stroke_color = np.array([0, 0, 0])
    stroke_width_px = 0

    if len(text_px) > 10:
        # テキストマスクを膨張させて縁取り候補を取得
        kernel_3 = np.ones((3, 3), np.uint8)
        kernel_5 = np.ones((5, 5), np.uint8)
        dilated_3 = cv2.dilate(text_pixels_mask, kernel_3)
        dilated_5 = cv2.dilate(text_pixels_mask, kernel_5)

        # 縁取り候補 = 膨張マスク AND NOT テキストマスク
        border_3 = cv2.bitwise_and(dilated_3, cv2.bitwise_not(text_pixels_mask))
        border_5 = cv2.bitwise_and(dilated_5, cv2.bitwise_not(text_pixels_mask))

        border_px_3 = roi[border_3 > 0]
        border_px_5 = roi[border_5 > 0]

        # 縁取りピクセルが十分暗い → 縁取りあり
        if len(border_px_3) > 5:
            border_lum_3 = _luminance(border_px_3).mean()
            if border_lum_3 < 80:  # 暗い → 縁取りあり
                stroke_detected = True
                stroke_color = _dominant_color(border_px_3, k=2)
                # 幅推定: 3px vs 5px でどちらが暗いかで判定
                if len(border_px_5) > 5:
                    border_lum_5 = _luminance(border_px_5).mean()
                    stroke_width_px = 4 if border_lum_5 < border_lum_3 + 20 else 2

    # ── グロー検出 ─────────────────────────────────────────────────────────
    glow_detected = False
    glow_color = np.array([255, 255, 255])

    if len(text_px) > 10:
        # テキストマスクをガウシアンブラーで広げる
        blurred = cv2.GaussianBlur(text_pixels_mask.astype(np.float32), (15, 15), 0)
        glow_region = (blurred > 10).astype(np.uint8) * 255
        glow_only = cv2.bitwise_and(glow_region, cv2.bitwise_not(text_pixels_mask))
        glow_only = cv2.bitwise_and(glow_only, cv2.bitwise_not(
            cv2.dilate(text_pixels_mask, np.ones((5, 5), np.uint8))
        ))
        glow_px = roi[glow_only > 0]
        if len(glow_px) > 20:
            glow_lum = _luminance(glow_px).mean()
            # グロー候補が縁取りより明るい場合のみグロー判定
            bg_lum = _luminance(roi).mean()
            if glow_lum > bg_lum + 15 and (not stroke_detected or glow_lum > 80):
                glow_detected = True
                glow_color = _dominant_color(glow_px, k=2)

    # ── 座布団（背景ハイライトボックス）検出 ─────────────────────────────
    background_box_detected = False
    background_box_color = np.array([0, 0, 0])
    background_box_opacity = 0.0

    # テキストマスクの外側（内側のみ）で均一な色があるか調べる
    non_text_inner = cv2.bitwise_and(
        cv2.bitwise_not(text_pixels_mask), inner_mask
    )
    non_text_px = roi[non_text_inner > 0]

    if len(non_text_px) > 20:
        # 色の分散が低い → 均一 → 座布団の可能性
        std_b = float(non_text_px[:, 0].std())
        std_g = float(non_text_px[:, 1].std())
        std_r = float(non_text_px[:, 2].std())
        color_variance = (std_b + std_g + std_r) / 3.0

        if color_variance < 40:  # 均一な色
            box_color = _dominant_color(non_text_px, k=1)
            box_lum = float(_luminance(box_color.reshape(1, 1, 3))[0, 0])
            # 背景が黒に近い or 明るいハイライトなら座布団とみなす
            if box_lum < 60 or box_lum > 180:
                background_box_detected = True
                background_box_color = box_color
                # 不透明度推定: 黒座布団なら輝度が低いほど不透明度高い
                if box_lum < 60:
                    background_box_opacity = round(1.0 - box_lum / 255.0, 2)
                else:
                    background_box_opacity = round(box_lum / 255.0, 2)

    return {
        "text_color": text_color.tolist(),
        "stroke_detected": stroke_detected,
        "stroke_color": stroke_color.tolist(),
        "stroke_width_px": stroke_width_px,
        "glow_detected": glow_detected,
        "glow_color": glow_color.tolist(),
        "background_box_detected": background_box_detected,
        "background_box_color": background_box_color.tolist(),
        "background_box_opacity": background_box_opacity,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 3. 行ごとの色違い検出
# ──────────────────────────────────────────────────────────────────────────────

def _detect_multicolor_lines(
    frame: np.ndarray,
    rx: int, ry: int, rw: int, rh: int,
) -> dict:
    """テキスト領域を上半分/下半分に分けて色が変わるか調べる。"""
    h_frame, w_frame = frame.shape[:2]
    x1, y1 = max(0, rx), max(0, ry)
    x2, y2 = min(w_frame, rx + rw), min(h_frame, ry + rh)
    if y2 - y1 < 10 or x2 - x1 < 5:
        return {"multicolor_lines": False, "line_colors_hex": []}

    roi = frame[y1:y2, x1:x2]
    lum = _luminance(roi)
    _, text_mask = cv2.threshold(lum, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    mid = (y2 - y1) // 2
    top_px = roi[:mid][text_mask[:mid] > 0]
    bot_px = roi[mid:][text_mask[mid:] > 0]

    if len(top_px) < 5 or len(bot_px) < 5:
        return {"multicolor_lines": False, "line_colors_hex": []}

    top_color = _dominant_color(top_px, k=2)
    bot_color = _dominant_color(bot_px, k=2)

    # 色差（L1距離）が大きければ色違い
    color_diff = float(np.abs(top_color.astype(float) - bot_color.astype(float)).mean())
    multicolor = color_diff > 30

    return {
        "multicolor_lines": multicolor,
        "line_colors_hex": [_bgr_to_hex(top_color), _bgr_to_hex(bot_color)] if multicolor else [],
    }


def export_subtitle_style_review_assets(
    cap: cv2.VideoCapture,
    fps: float,
    cuts: list[dict],
    text_regions: list[dict],
    video_width: int,
    video_height: int,
    output_dir: Path,
    source_video: str | None = None,
    max_samples: int = 12,
) -> dict:
    """
    字幕スタイルの変化がありそうなカットごとに、代表スクリーンショットと crop を保存する。

    Returns:
        analysis.json に埋め込める review メタデータ。
    """
    samples_dir = output_dir / "subtitle_style_samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    subtitle_regions = [
        region for region in text_regions
        if region.get("confidence", 0) >= 60 and len(str(region.get("text", "")).strip()) >= 2
    ]
    if not subtitle_regions or not cuts:
        return {
            "preferred_source": "heuristic_only",
            "review_status": "skipped",
            "reason": "no_subtitle_regions",
            "samples_dir": str(samples_dir),
            "sample_count": 0,
            "manifest_path": None,
            "review_template_path": None,
        }

    candidates: list[dict] = []
    for cut_index, cut in enumerate(cuts):
        start_frame = int(cut.get("start_frame", 0))
        end_frame = int(cut.get("end_frame", start_frame))
        cut_regions = [
            region for region in subtitle_regions
            if start_frame <= int(region.get("frame", -1)) < end_frame
        ]
        if not cut_regions:
            continue

        regions_by_frame: dict[int, list[dict]] = {}
        for region in cut_regions:
            frame_number = int(region.get("frame", 0))
            regions_by_frame.setdefault(frame_number, []).append(region)

        if not regions_by_frame:
            continue

        cut_mid_frame = (start_frame + end_frame) / 2

        def _frame_score(item: tuple[int, list[dict]]) -> tuple[float, float, float]:
            frame_number, frame_regions = item
            confidence_sum = sum(float(r.get("confidence", 0)) for r in frame_regions)
            text_len = sum(len(str(r.get("text", ""))) for r in frame_regions)
            distance_penalty = abs(frame_number - cut_mid_frame)
            return (confidence_sum, text_len, -distance_penalty)

        representative_frame, frame_regions = max(regions_by_frame.items(), key=_frame_score)
        bbox = _combine_regions_bbox(frame_regions, video_width, video_height)

        cap.set(cv2.CAP_PROP_POS_FRAMES, representative_frame)
        ret, frame = cap.read()
        if not ret:
            continue

        feature = _analyze_frame_region(frame, *bbox)
        multicolor = _detect_multicolor_lines(frame, *bbox)
        feature.update(multicolor)
        feature["text_color_hex"] = _bgr_to_hex(tuple(feature.get("text_color", [255, 255, 255])))
        bg_box_color = feature.get("background_box_color")
        feature["background_box_color_hex"] = (
            _bgr_to_hex(tuple(bg_box_color))
            if feature.get("background_box_detected") and bg_box_color is not None
            else None
        )

        signature = _build_style_signature(feature, bbox, video_height)
        x1, y1, w1, h1 = bbox
        text_preview = " ".join(str(r.get("text", "")).strip() for r in frame_regions if str(r.get("text", "")).strip())
        time_seconds = round(representative_frame / max(fps, 1.0), 3)
        y_percent = round(((y1 + h1 / 2) / max(video_height, 1)) * 100, 1)

        candidates.append({
            "cut_index": cut_index,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "frame": representative_frame,
            "time_seconds": time_seconds,
            "bbox": bbox,
            "frame_image": frame.copy(),
            "style_signature": signature,
            "text_preview": text_preview[:120],
            "heuristic": {
                "zone": _subtitle_zone_label(y_percent),
                "yPercent": y_percent,
                "text_color_hex": feature.get("text_color_hex"),
                "stroke_detected": bool(feature.get("stroke_detected")),
                "stroke_width_px": int(feature.get("stroke_width_px", 0) or 0),
                "stroke_color_hex": _bgr_to_hex(tuple(feature.get("stroke_color", [0, 0, 0])))
                if feature.get("stroke_detected") else None,
                "background_box_detected": bool(feature.get("background_box_detected")),
                "background_box_color_hex": feature.get("background_box_color_hex"),
                "multicolor_lines": bool(feature.get("multicolor_lines")),
                "line_colors_hex": feature.get("line_colors_hex", []),
            },
        })

    selected: list[dict] = []
    last_signature: str | None = None
    for candidate in candidates:
        if candidate["style_signature"] == last_signature:
            continue
        selected.append(candidate)
        last_signature = candidate["style_signature"]
        if len(selected) >= max_samples:
            break

    if not selected and candidates:
        selected = [candidates[0]]

    samples: list[dict] = []
    for index, candidate in enumerate(selected, start=1):
        sample_id = f"style_{index:02d}"
        frame_image = candidate.pop("frame_image")
        x1, y1, w1, h1 = candidate["bbox"]
        crop_pad = 24
        x_start = max(0, x1 - crop_pad)
        y_start = max(0, y1 - crop_pad)
        x_end = min(video_width, x1 + w1 + crop_pad)
        y_end = min(video_height, y1 + h1 + crop_pad)
        crop = frame_image[y_start:y_end, x_start:x_end]

        full_frame_path = samples_dir / f"{sample_id}_full.jpg"
        crop_path = samples_dir / f"{sample_id}_crop.jpg"
        cv2.imwrite(str(full_frame_path), frame_image)
        cv2.imwrite(str(crop_path), crop)

        samples.append({
            "id": sample_id,
            "cut_index": candidate["cut_index"],
            "cut_range": f"{candidate['start_frame']}-{candidate['end_frame']}",
            "frame": candidate["frame"],
            "time_seconds": candidate["time_seconds"],
            "text_preview": candidate["text_preview"],
            "style_signature": candidate["style_signature"],
            "heuristic": candidate["heuristic"],
            "full_frame_path": str(full_frame_path),
            "subtitle_crop_path": str(crop_path),
        })

    manifest_path = samples_dir / "manifest.json"
    review_template_path = output_dir / "subtitle_style_template.json"
    readme_path = samples_dir / "REVIEW.md"

    manifest = {
        "version": 1,
        "mode": "agent_review_preferred",
        "selection_rule": "first subtitle cut after coarse visual signature change",
        "source_video": source_video,
        "sample_count": len(samples),
        "samples": samples,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_review_template(review_template_path, manifest_path, source_video, samples)
    _write_review_readme(readme_path, review_template_path, samples)

    return {
        "preferred_source": "agent_review",
        "review_status": "pending",
        "samples_dir": str(samples_dir),
        "sample_count": len(samples),
        "manifest_path": str(manifest_path),
        "review_template_path": str(review_template_path),
        "review_readme_path": str(readme_path),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 4. メインエントリポイント
# ──────────────────────────────────────────────────────────────────────────────

def analyze_subtitle_visual_style(
    cap: cv2.VideoCapture,
    fps: float,
    text_regions: list[dict],
    video_width: int,
    video_height: int,
    max_samples: int = 12,
) -> dict:
    """
    Layer 4 エントリポイント。

    Args:
        cap            : OpenCV VideoCapture（解析済みを想定）
        fps            : 動画フレームレート
        text_regions   : Layer 1 で検出したテキスト領域リスト
        video_width    : 動画幅 (px)
        video_height   : 動画高さ (px)
        max_samples    : 分析するフレーム数上限

    Returns: dict（analysis.json の subtitle_visual キーに格納する）
    """
    # ── フォントサイズ推定（座標ベース・高速） ────────────────────────────
    font_size_result = _estimate_font_size(text_regions, video_height, video_width)

    if not text_regions:
        return {
            **font_size_result,
            "text_color_hex": "#ffffff",
            "stroke_detected": False,
            "stroke_width_px": 0,
            "stroke_color_hex": "#000000",
            "glow_detected": False,
            "glow_color_hex": None,
            "background_box_detected": False,
            "background_box_color_hex": None,
            "background_box_opacity": None,
            "multicolor_lines": False,
            "line_colors_hex": [],
            "confidence": "low",
        }

    # ── 代表フレームをサンプリング ─────────────────────────────────────────
    # text_regions を frame 番号でソートして均等サンプリング
    sorted_regions = sorted(text_regions, key=lambda r: r.get("frame", 0))
    step = max(1, len(sorted_regions) // max_samples)
    sampled = sorted_regions[::step][:max_samples]

    frame_results: list[dict] = []
    multicolor_results: list[dict] = []

    for region in tqdm(sampled, desc="    字幕ビジュアル", unit="frame", leave=False, ncols=60):
        frame_idx = region.get("frame", 0)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue

        # text_region の座標を絶対 px に変換
        # pytesseract は左上基準 (left, top, width, height) をそのまま px で返す
        rx = int(region.get("x", 0) * video_width) if region.get("x", 0) <= 1.0 else int(region.get("left", 0))
        ry = int(region.get("y", 0) * video_height) if region.get("y", 0) <= 1.0 else int(region.get("top", 0))
        # text_regions の x/y が中心座標の場合は変換
        tw = int(region.get("width", 0) * video_width) if region.get("width", 0) <= 1.0 else int(region.get("width", 50))
        th = int(region.get("height", 0) * video_height) if region.get("height", 0) <= 1.0 else int(region.get("height", 30))

        # x/y が中心座標として記録されている場合（video_structure.py の形式に合わせる）
        # video_structure.py では x_c / y_c を x / y として保存
        # → 中心からバウンディングボックスに変換
        if "width" not in region and tw == 0:
            tw = 80
        if "height" not in region and th == 0:
            th = 40
        rx = max(0, rx - tw // 2)
        ry = max(0, ry - th // 2)

        if tw < 5 or th < 5:
            continue

        result = _analyze_frame_region(frame, rx, ry, tw, th)
        if result:
            frame_results.append(result)

        mc = _detect_multicolor_lines(frame, rx, ry, tw, th)
        multicolor_results.append(mc)

    if not frame_results:
        return {
            **font_size_result,
            "text_color_hex": "#ffffff",
            "stroke_detected": False,
            "stroke_width_px": 0,
            "stroke_color_hex": "#000000",
            "glow_detected": False,
            "glow_color_hex": None,
            "background_box_detected": False,
            "background_box_color_hex": None,
            "background_box_opacity": None,
            "multicolor_lines": False,
            "line_colors_hex": [],
            "confidence": "low",
        }

    # ── 結果を集計（多数決） ──────────────────────────────────────────────
    def _majority(key: str) -> bool:
        vals = [r[key] for r in frame_results if key in r]
        return sum(vals) > len(vals) / 2

    def _median_color(key: str, default: list[int]) -> np.ndarray:
        colors = [r[key] for r in frame_results if key in r and r[key] is not None]
        if not colors:
            return np.array(default)
        return np.array(colors).mean(axis=0).astype(np.uint8)

    def _median_val(key: str, default: float) -> float:
        vals = [r[key] for r in frame_results if key in r and r[key] is not None]
        return float(np.median(vals)) if vals else default

    stroke_detected = _majority("stroke_detected")
    glow_detected = _majority("glow_detected")
    bg_box_detected = _majority("background_box_detected")

    text_color = _median_color("text_color", [255, 255, 255])
    stroke_color = _median_color("stroke_color", [0, 0, 0]) if stroke_detected else np.array([0, 0, 0])
    glow_color = _median_color("glow_color", [255, 255, 255]) if glow_detected else None
    bg_box_color = _median_color("background_box_color", [0, 0, 0]) if bg_box_detected else None
    bg_box_opacity = round(_median_val("background_box_opacity", 0.0), 2) if bg_box_detected else None
    stroke_width = int(round(_median_val("stroke_width_px", 2))) if stroke_detected else 0

    # 行ごと色違い
    mc_flags = [r["multicolor_lines"] for r in multicolor_results]
    multicolor = sum(mc_flags) > len(mc_flags) / 2
    line_colors: list[str] = []
    if multicolor:
        mc_with_colors = [r for r in multicolor_results if r.get("multicolor_lines") and r.get("line_colors_hex")]
        if mc_with_colors:
            # 最多数の行色リストを採用
            line_colors = mc_with_colors[len(mc_with_colors) // 2]["line_colors_hex"]

    # 座布団の rgba 文字列生成
    bg_box_rgba = None
    if bg_box_detected and bg_box_color is not None and bg_box_opacity is not None:
        b, g, r = int(bg_box_color[0]), int(bg_box_color[1]), int(bg_box_color[2])
        bg_box_rgba = f"rgba({r},{g},{b},{bg_box_opacity})"

    confidence = "high" if len(frame_results) >= 5 else "medium" if len(frame_results) >= 2 else "low"

    return {
        **font_size_result,
        "text_color_hex": _bgr_to_hex(tuple(text_color)),
        "stroke_detected": stroke_detected,
        "stroke_width_px": stroke_width,
        "stroke_color_hex": _bgr_to_hex(tuple(stroke_color)) if stroke_detected else None,
        "glow_detected": glow_detected,
        "glow_color_hex": _bgr_to_hex(tuple(glow_color)) if glow_detected and glow_color is not None else None,
        "background_box_detected": bg_box_detected,
        "background_box_color_hex": _bgr_to_hex(tuple(bg_box_color)) if bg_box_detected and bg_box_color is not None else None,
        "background_box_rgba": bg_box_rgba,
        "background_box_opacity": bg_box_opacity,
        "multicolor_lines": multicolor,
        "line_colors_hex": line_colors,
        "samples_analyzed": len(frame_results),
        "confidence": confidence,
    }
