import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export type CameraMotionType =
  | "zoom_in"    // ゆるやかなズームイン（Ken Burns）
  | "zoom_out"   // ズームアウト
  | "pan_right"  // 右へパン
  | "pan_left"   // 左へパン
  | "tilt_up"    // 上へチルト
  | "tilt_down"  // 下へチルト
  | "shake"      // カメラシェイク
  | "static";    // 静止

interface ImageSceneProps {
  src: string;
  /** @deprecated kenBurns は motionType="zoom_in" に統一。後方互換のため残す */
  kenBurns?: boolean;
  zoomStart?: number;
  zoomEnd?: number;
  originX?: number;       // 変形の基点 X (0-1), デフォルト 0.5
  originY?: number;       // 変形の基点 Y (0-1), デフォルト 0.4
  motionType?: CameraMotionType;
  motionIntensity?: number; // 0.0–2.0 (1.0=標準, 大きいほど激しい)
}

export const ImageScene: React.FC<ImageSceneProps> = ({
  src,
  kenBurns = true,
  zoomStart = 1.0,
  zoomEnd = 1.07,
  originX = 0.5,
  originY = 0.4,
  motionType,
  motionIntensity = 1.0,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 後方互換: motionType 未指定で kenBurns=true の場合は zoom_in とみなす
  const effectiveMotion: CameraMotionType =
    motionType ?? (kenBurns ? "zoom_in" : "static");

  const t = durationInFrames > 1
    ? interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: "clamp" })
    : 0;

  // intensity でスケーリングする移動量の基準値
  const panAmount  = 4 * motionIntensity; // % (translateX/Y の最大値)
  const zoomAmount = 0.08 * motionIntensity; // 倍率差

  let scale  = 1;
  let transX = 0; // %
  let transY = 0; // %

  switch (effectiveMotion) {
    case "zoom_in":
      scale = interpolate(t, [0, 1], [zoomStart, zoomStart + zoomAmount]);
      break;

    case "zoom_out":
      scale = interpolate(t, [0, 1], [zoomStart + zoomAmount, zoomStart]);
      break;

    case "pan_right":
      scale = 1 + zoomAmount * 0.5; // 少しズームして余白を作る
      transX = interpolate(t, [0, 1], [-panAmount, panAmount]);
      break;

    case "pan_left":
      scale = 1 + zoomAmount * 0.5;
      transX = interpolate(t, [0, 1], [panAmount, -panAmount]);
      break;

    case "tilt_up":
      scale = 1 + zoomAmount * 0.5;
      transY = interpolate(t, [0, 1], [panAmount, -panAmount]);
      break;

    case "tilt_down":
      scale = 1 + zoomAmount * 0.5;
      transY = interpolate(t, [0, 1], [-panAmount, panAmount]);
      break;

    case "shake": {
      // 高周波の微振動（sin波の重ね合わせ）
      const amp = 1.2 * motionIntensity;
      transX = Math.sin(frame * 0.9) * amp + Math.sin(frame * 1.7) * amp * 0.5;
      transY = Math.sin(frame * 1.1) * amp * 0.6 + Math.sin(frame * 2.3) * amp * 0.3;
      scale = 1 + zoomAmount * 0.3;
      break;
    }

    case "static":
    default:
      scale = 1;
      break;
  }

  return (
    <AbsoluteFill>
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${transX}%, ${transY}%)`,
          transformOrigin: `${originX * 100}% ${originY * 100}%`,
        }}
      />
    </AbsoluteFill>
  );
};
