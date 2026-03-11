"""
Layer 1: 動画構造解析
- シーンカット検出 (ヒストグラム比較)
- 顔検出 (mediapipe)
- テキスト領域検出 (pytesseract)
- カメラ動き解析 (オプティカルフロー)
"""
from __future__ import annotations
import cv2
import numpy as np
from pathlib import Path
from typing import Optional

try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False
    print("⚠️  mediapipe未インストール。顔検出をスキップします。")

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    def tqdm(it, **kw):  # type: ignore[misc]
        return it


# ─── シーンカット検出 ─────────────────────────────────────────────────────────

def detect_scene_cuts(cap: cv2.VideoCapture, fps: float, threshold: float = 0.35) -> list[dict]:
    """ヒストグラム相関によるシーンカット検出"""
    cuts: list[dict] = []
    prev_hist: Optional[np.ndarray] = None
    frame_idx = 0
    segment_start = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    bar = tqdm(total=total_frames, desc="    シーンカット", unit="f", leave=False, ncols=60)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

        if prev_hist is not None:
            diff = 1.0 - cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
            if diff > threshold:
                cuts.append({
                    "start": round(segment_start / fps, 3),
                    "end": round(frame_idx / fps, 3),
                    "start_frame": segment_start,
                    "end_frame": frame_idx,
                })
                segment_start = frame_idx

        prev_hist = hist.copy()
        frame_idx += 1
        bar.update(1)
    bar.close()

    # 最終セグメント
    cuts.append({
        "start": round(segment_start / fps, 3),
        "end": round(total_frames / fps, 3),
        "start_frame": segment_start,
        "end_frame": total_frames,
    })
    return cuts


# ─── 顔検出 ──────────────────────────────────────────────────────────────────

def detect_faces(cap: cv2.VideoCapture, fps: float, sample_every: int = 15) -> list[dict]:
    """mediapipe FaceDetection によるサンプリング顔検出"""
    if not HAS_MEDIAPIPE:
        return []

    faces_data: list[dict] = []
    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    with mp.solutions.face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5
    ) as detector:
        bar = tqdm(total=total_frames, desc="    顔検出    ", unit="f", leave=False, ncols=60)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_every == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = detector.process(rgb)
                if results.detections:
                    for det in results.detections:
                        box = det.location_data.relative_bounding_box
                        faces_data.append({
                            "frame": frame_idx,
                            "time": round(frame_idx / fps, 3),
                            "x": round(box.xmin + box.width / 2, 3),
                            "y": round(box.ymin + box.height / 2, 3),
                            "size": round(box.width * box.height, 3),
                            "confidence": round(det.score[0], 3),
                        })
            frame_idx += 1
            bar.update(1)
        bar.close()

    return faces_data


# ─── テキスト領域検出 ─────────────────────────────────────────────────────────

def detect_text_regions(
    cap: cv2.VideoCapture, fps: float, sample_every: int = 30, skip_ocr: bool = False
) -> list[dict]:
    """pytesseract によるテロップ位置検出"""
    if not HAS_TESSERACT or skip_ocr:
        return []

    text_regions: list[dict] = []
    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    bar = tqdm(total=total_frames, desc="    OCR       ", unit="f", leave=False, ncols=60)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            try:
                data = pytesseract.image_to_data(
                    gray,
                    output_type=pytesseract.Output.DICT,
                    config="--psm 11 -l jpn+eng",
                )
                for i, text in enumerate(data["text"]):
                    conf = int(data["conf"][i])
                    if text.strip() and conf > 50:
                        x_c = (data["left"][i] + data["width"][i] / 2) / w
                        y_c = (data["top"][i] + data["height"][i] / 2) / h
                        text_regions.append({
                            "frame": frame_idx,
                            "time": round(frame_idx / fps, 3),
                            "x": round(x_c, 3),
                            "y": round(y_c, 3),
                            "text": text.strip(),
                            "confidence": conf,
                        })
            except Exception:
                pass
        frame_idx += 1
        bar.update(1)
    bar.close()

    return text_regions


# ─── カメラ動き解析 ───────────────────────────────────────────────────────────

def _classify_motion(dx: float, dy: float, magnitude: float) -> str:
    if magnitude > 8:
        return "shake"
    if abs(dx) > abs(dy) * 1.5:
        return "pan_right" if dx > 0 else "pan_left"
    if abs(dy) > abs(dx) * 1.5:
        return "tilt_down" if dy > 0 else "tilt_up"
    return "zoom" if magnitude > 4 else "static"


def _merge_motions(motions: list[dict]) -> list[dict]:
    if not motions:
        return []
    merged: list[dict] = []
    cur = {"type": motions[0]["type"], "start": motions[0]["time"], "end": motions[0]["time"]}
    for m in motions[1:]:
        if m["type"] == cur["type"] and m["time"] - cur["end"] < 0.5:
            cur["end"] = round(m["time"], 3)
        else:
            merged.append(cur)
            cur = {"type": m["type"], "start": m["time"], "end": m["time"]}
    merged.append(cur)
    return merged


def analyze_camera_motion(cap: cv2.VideoCapture, fps: float, sample_every: int = 5) -> list[dict]:
    """Lucas-Kanade オプティカルフローによるカメラ動き推定"""
    raw_motions: list[dict] = []
    prev_gray: Optional[np.ndarray] = None
    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    bar = tqdm(total=total_frames, desc="    カメラ動き ", unit="f", leave=False, ncols=60)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every == 0:
            gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (320, 180))
            if prev_gray is not None:
                pts = cv2.goodFeaturesToTrack(prev_gray, 100, 0.3, 7)
                if pts is not None:
                    npts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, pts, None)
                    good = (status.flatten() == 1)
                    if good.sum() > 5:
                        flow = npts[good] - pts[good]
                        mean_flow = np.mean(flow, axis=0)
                        mag = float(np.linalg.norm(mean_flow))
                        if mag > 2.0:
                            raw_motions.append({
                                "time": round(frame_idx / fps, 3),
                                "type": _classify_motion(mean_flow[0][0], mean_flow[0][1], mag),
                                "magnitude": round(mag, 3),
                            })
            prev_gray = gray.copy()
        frame_idx += 1
        bar.update(1)
    bar.close()

    return _merge_motions(raw_motions)


# ─── カメラモーション × シーンカット マッチング ───────────────────────────────

def assign_motion_to_cuts(
    cuts: list[dict], camera_motion: list[dict]
) -> list[dict]:
    """
    各シーンカットに対してその区間で最も支配的なカメラモーションタイプを付与する。

    camera_motion の各エントリ: {"type": str, "start": float, "end": float, "magnitude"?: float}
    cuts の各エントリ: {"start": float, "end": float, ...}

    Returns: cuts に "motion_type" / "motion_intensity" / "origin_x" / "origin_y" を追加したリスト
    """
    # magnitude の正規化係数（最大 magnitude を 1.0 に）
    all_mags = [m.get("magnitude", 1.0) for m in camera_motion if "magnitude" in m]
    max_mag = max(all_mags) if all_mags else 1.0
    if max_mag == 0:
        max_mag = 1.0

    # pan 方向からズーム基点を推定するマップ
    _ORIGIN_MAP = {
        "pan_right": (0.3, 0.5),   # 右パン → 基点は左寄り
        "pan_left":  (0.7, 0.5),   # 左パン → 基点は右寄り
        "tilt_up":   (0.5, 0.7),   # 上チルト → 基点は下
        "tilt_down": (0.5, 0.3),   # 下チルト → 基点は上
        "zoom":      (0.5, 0.4),
        "shake":     (0.5, 0.5),
        "static":    (0.5, 0.5),
    }

    enriched_cuts = []
    for cut in cuts:
        cut_start = cut.get("start", 0.0)
        cut_end   = cut.get("end", 0.0)
        overlap_motions: list[dict] = []

        for m in camera_motion:
            m_start = m.get("start", 0.0)
            m_end   = m.get("end",   m_start)
            # 重複区間あり？
            if m_end > cut_start and m_start < cut_end:
                overlap_motions.append(m)

        if not overlap_motions:
            motion_type = "zoom_in"
            intensity   = 1.0
        else:
            # 支配的なタイプを多数決（magnitude 加重）
            type_score: dict[str, float] = {}
            for m in overlap_motions:
                t = m.get("type", "static")
                # zoom → zoom_in に正規化
                if t == "zoom":
                    t = "zoom_in"
                mag = m.get("magnitude", 1.0) / max_mag
                type_score[t] = type_score.get(t, 0.0) + mag

            motion_type = max(type_score, key=lambda k: type_score[k])
            intensity   = round(min(2.0, type_score[motion_type] / max(len(overlap_motions), 1) * 2.0), 2)

        origin_x, origin_y = _ORIGIN_MAP.get(motion_type, (0.5, 0.4))

        enriched_cuts.append({
            **cut,
            "motion_type": motion_type,
            "motion_intensity": intensity,
            "origin_x": origin_x,
            "origin_y": origin_y,
        })

    return enriched_cuts


# ─── メイン ───────────────────────────────────────────────────────────────────

def analyze_video_structure(
    video_path: Path, frames_dir: Path, skip_ocr: bool = False
) -> dict:
    """Layer 1 エントリポイント"""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"動画を開けません: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print("    シーンカット検出中...")
    cuts = detect_scene_cuts(cap, fps)

    print("    顔検出中...")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    faces = detect_faces(cap, fps)

    print("    テキスト領域検出中...")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    text_regions = detect_text_regions(cap, fps, skip_ocr=skip_ocr)

    print("    カメラ動き解析中...")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    camera_motion = analyze_camera_motion(cap, fps)

    print("    カメラモーション × シーンカット マッチング中...")
    enriched_cuts = assign_motion_to_cuts(cuts, camera_motion)

    cap.release()

    # 重要フレーム（カット境界 + 大きな顔 + テキスト）
    important_frames = sorted(set(
        [c["start_frame"] for c in cuts]
        + [f["frame"] for f in faces if f["size"] > 0.1]
        + [t["frame"] for t in text_regions]
    ))[:30]

    return {
        "duration": round(duration, 3),
        "fps": round(fps, 2),
        "resolution": {"width": width, "height": height},
        "video_structure": {
            "cuts": enriched_cuts,
            "faces": faces[:50],
            "text_regions": text_regions[:100],
            "camera_motion": camera_motion,
            "important_frames": important_frames,
        },
    }
