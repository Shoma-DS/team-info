#!/usr/bin/env python3
"""
upscale_materials: materials/ 直下の採用画像を一括でローカル補正する。

用途:
  1. fetch_materials.py で自動取得
  2. 不足分をユーザーが手動で配置
  3. 素材が揃った後、このスクリプトで一括アップスケール

無料のローカル処理のみを使い、OpenCV ベースで
「拡大 + 軽いコントラスト補正 + 軽いシャープ化」を行う。
AI 超解像ではないため、元画像の情報量そのものは増えない。
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_repo_root

PROJECT_ROOT = get_repo_root()

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
SLOT_NAMES = [
    "00_hook",
    "01_opening",
    "02_s1_1", "02_s1_2", "02_s1_3",
    "03_s2_1", "03_s2_2", "03_s2_3",
    "04_s3_1", "04_s3_2", "04_s3_3",
    "99_cta",
]
DEFAULT_TARGET_LONG_SIDE = 2160
DEFAULT_MAX_SCALE = 2.0


@dataclass
class UpscaleResult:
    file: str
    original_width: int
    original_height: int
    output_width: int
    output_height: int
    scale_applied: float
    backup_path: str


def import_cv2():
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "cv2 / numpy が見つかりません。"
            " team_info_runtime.py run-remotion-python 経由で実行してください。"
        ) from exc
    return cv2, np


def find_slot_image(materials_dir: Path, slot: str) -> Path | None:
    for ext in ALLOWED_EXTENSIONS:
        candidate = materials_dir / f"{slot}{ext}"
        if candidate.exists():
            return candidate
    return None


def resolve_target_files(materials_dir: Path, allow_incomplete: bool) -> list[Path]:
    files: list[Path] = []
    missing: list[str] = []

    for slot in SLOT_NAMES:
        image_path = find_slot_image(materials_dir, slot)
        if image_path:
            files.append(image_path)
        else:
            missing.append(slot)

    if not files:
        print("採用画像スロットが見つからないため、アップスケールを中止します。")
        raise SystemExit(1)

    if missing and not allow_incomplete:
        print("未検出スロットがありますが、このフォルダに存在する採用画像だけ処理します。")
        for slot in missing:
            print(f"  - {slot}")
        print("このコンポジションで未使用のスロットなら問題ありません。")

    if missing and allow_incomplete:
        print("不足スロットがありますが、存在するファイルだけ処理します。")
        for slot in missing:
            print(f"  - {slot}")

    return files


def read_image(image_path: Path):
    cv2, np = import_cv2()
    buffer = np.fromfile(str(image_path), dtype=np.uint8)
    if buffer.size == 0:
        raise RuntimeError("ファイルが空です。")
    image = cv2.imdecode(buffer, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise RuntimeError("画像を読み込めませんでした。")
    return image


def write_image(image_path: Path, image) -> None:
    cv2, _ = import_cv2()
    suffix = image_path.suffix.lower()

    if suffix in (".jpg", ".jpeg"):
        ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    elif suffix == ".png":
        ok, encoded = cv2.imencode(".png", image, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])
    elif suffix == ".webp":
        ok, encoded = cv2.imencode(".webp", image, [int(cv2.IMWRITE_WEBP_QUALITY), 95])
    else:
        raise RuntimeError(f"未対応の拡張子です: {suffix}")

    if not ok:
        raise RuntimeError("画像エンコードに失敗しました。")
    encoded.tofile(str(image_path))


def split_alpha(image):
    if len(image.shape) == 2:
        return image, None
    if image.shape[2] == 4:
        return image[:, :, :3], image[:, :, 3]
    return image, None


def merge_alpha(image, alpha):
    if alpha is None:
        return image
    cv2, _ = import_cv2()
    return cv2.merge([image[:, :, 0], image[:, :, 1], image[:, :, 2], alpha])


def apply_clahe_and_denoise(image):
    cv2, _ = import_cv2()
    if len(image.shape) == 2:
        clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        return cv2.GaussianBlur(enhanced, (0, 0), 0.3)

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge([l_channel, a_channel, b_channel])
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return cv2.bilateralFilter(enhanced, d=5, sigmaColor=30, sigmaSpace=30)


def unsharp_mask(image):
    cv2, _ = import_cv2()
    blurred = cv2.GaussianBlur(image, (0, 0), 1.1)
    return cv2.addWeighted(image, 1.18, blurred, -0.18, 0)


def upscale_image(image, target_long_side: int, max_scale: float):
    cv2, _ = import_cv2()
    height, width = image.shape[:2]
    long_side = max(width, height)
    required_scale = max(1.0, target_long_side / long_side)
    scale = min(max_scale, required_scale)

    base, alpha = split_alpha(image)
    processed = apply_clahe_and_denoise(base)

    if scale > 1.001:
        new_width = max(1, int(round(width * scale)))
        new_height = max(1, int(round(height * scale)))
        processed = cv2.resize(processed, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        if alpha is not None:
            alpha = cv2.resize(alpha, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    processed = unsharp_mask(processed)
    output = merge_alpha(processed, alpha)
    out_height, out_width = output.shape[:2]
    return output, scale, out_width, out_height


def upscale_materials(
    materials_dir: Path,
    target_long_side: int,
    max_scale: float,
    allow_incomplete: bool,
) -> list[UpscaleResult]:
    target_files = resolve_target_files(materials_dir, allow_incomplete=allow_incomplete)
    if not target_files:
        print("対象画像が見つかりませんでした。")
        return []

    backup_root = materials_dir / "_upscale_backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root.mkdir(parents=True, exist_ok=True)
    results: list[UpscaleResult] = []

    print(f"対象枚数: {len(target_files)}")
    print(f"バックアップ先: {backup_root}")

    for image_path in target_files:
        original = read_image(image_path)
        original_height, original_width = original.shape[:2]
        backup_path = backup_root / image_path.name
        backup_path.write_bytes(image_path.read_bytes())

        output, scale, output_width, output_height = upscale_image(
            original,
            target_long_side=target_long_side,
            max_scale=max_scale,
        )
        write_image(image_path, output)

        result = UpscaleResult(
            file=image_path.name,
            original_width=original_width,
            original_height=original_height,
            output_width=output_width,
            output_height=output_height,
            scale_applied=round(scale, 4),
            backup_path=str(backup_path),
        )
        results.append(result)
        print(
            f"  - {image_path.name}: "
            f"{original_width}x{original_height} -> {output_width}x{output_height} "
            f"(scale={result.scale_applied})"
        )

    report_path = materials_dir / "upscale_report.json"
    report_path.write_text(
        json.dumps(
            {
                "materials_dir": str(materials_dir),
                "target_long_side": target_long_side,
                "max_scale": max_scale,
                "processed_count": len(results),
                "processed": [asdict(result) for result in results],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"レポート出力: {report_path}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="materials/ の採用画像をまとめてローカル補正する"
    )
    parser.add_argument("--materials-dir", type=Path)
    parser.add_argument("--output-title", type=str, default="")
    parser.add_argument("--target-long-side", type=int, default=DEFAULT_TARGET_LONG_SIDE)
    parser.add_argument("--max-scale", type=float, default=DEFAULT_MAX_SCALE)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    if args.materials_dir:
        materials_dir = args.materials_dir
    elif args.output_title:
        materials_dir = (
            PROJECT_ROOT / "inputs" / "viral-analysis" / "output" / args.output_title / "materials"
        )
    else:
        print("materials フォルダのパスを入力してください:")
        materials_dir = Path(input("> ").strip())

    upscale_materials(
        materials_dir=materials_dir,
        target_long_side=max(args.target_long_side, 1),
        max_scale=max(args.max_scale, 1.0),
        allow_incomplete=args.allow_incomplete,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
