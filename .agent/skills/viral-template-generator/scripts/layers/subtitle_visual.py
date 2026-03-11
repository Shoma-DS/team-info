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
