#!/usr/bin/env python3
"""
天使の羽画像をパーツ分割して透過PNGとして保存する
背景除去: HSV彩度で判別 (背景=青みS高、羽=白S低)
  - angel-wing-right.png
  - angel-wing-left.png
  - angel-halo.png
"""

from PIL import Image, ImageFilter
import numpy as np
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parents[1] / "my-video/public/assets/channels/acoriel/common"
SRC = ASSET_DIR / "angel-wings.png"
OUT = ASSET_DIR


def remove_bg(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    hsv  = img.convert("HSV")

    data = np.array(rgba, dtype=np.uint8)
    h_arr = np.array(hsv)

    S = h_arr[:, :, 1].astype(float)  # 背景≈50-55、羽≈0-20
    V = h_arr[:, :, 2].astype(float)  # 輝度

    # 彩度が低い(白い)かつ輝度が高いほど前景
    # S < 25 & V > 160 → 前景  /  S > 48 → 背景
    s_lo, s_hi = 22.0, 46.0
    score = 1.0 - np.clip((S - s_lo) / (s_hi - s_lo), 0.0, 1.0)

    # 輝度補正: V が低すぎる画素はどちらでも透明気味に
    v_factor = np.clip((V - 140) / 80.0, 0.0, 1.0)
    score = score * v_factor

    alpha = np.clip(score * 255, 0, 255).astype(np.uint8)

    # 細かいゴミを除去: 低アルファは完全透明に
    alpha = np.where(alpha < 50, 0, alpha)
    alpha = np.where(alpha > 200, 255, alpha)

    # 軽くブラーしてエッジを滑らかに
    alpha_img  = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.7))
    data[:, :, 3] = np.array(alpha_img)
    return Image.fromarray(data)


def main():
    print(f"Loading: {SRC}")
    img = Image.open(SRC).convert("RGB")
    w, h = img.size
    print(f"Image size: {w}x{h}")

    print("Removing background (saturation-based)...")
    rgba = remove_bg(img)

    # ── 切り出し座標 ─────────────────────────────────
    # 画像: 259x194
    #   ハロー: 上部中央   y:2〜h*0.33,  x:w*0.23〜w*0.77
    #   左羽:  左側        y:h*0.03〜h,  x:0〜w*0.56
    #   右羽:  右側        y:h*0.03〜h,  x:w*0.44〜w

    parts = {
        "angel-halo.png":       (int(w*0.23), 2,           int(w*0.77), int(h*0.33)),
        "angel-wing-left.png":  (0,           int(h*0.03), int(w*0.56), h),
        "angel-wing-right.png": (int(w*0.44), int(h*0.03), w,           h),
    }

    for filename, box in parts.items():
        part = rgba.crop(box)
        out_path = OUT / filename
        part.save(out_path, "PNG")
        # 確認用に非透過版も保存
        checker = Image.new("RGB", part.size, (200, 200, 200))
        checker.paste(part, mask=part.split()[3])
        print(f"Saved: {out_path}  size={part.size}")

    print("Done!")


if __name__ == "__main__":
    main()
