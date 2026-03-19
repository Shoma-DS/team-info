import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type CameraMotionType =
  | "zoom_in"    // ゆるやかなズームイン（Ken Burns）
  | "zoom_out"   // ズームアウト
  | "pan_right"  // 右へパン
  | "pan_left"   // 左へパン
  | "tilt_up"    // 上へチルト
  | "tilt_down"  // 下へチルト
  | "shake"      // カメラシェイク
  | "static";    // 静止

export type CameraMotionProfile =
  | "standard"   // 既存相当
  | "gentle"     // 超低速ズーム/パン
  | "still";     // 完全静止

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
  motionProfile?: CameraMotionProfile; // "gentle" で静止寄り、"still" で完全静止
  baseScale?: number; // GUI 微調整用のベース倍率
  cropXPercent?: number; // object-position の中心からのずらし量
  cropYPercent?: number; // object-position の中心からのずらし量
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
  motionProfile = "standard",
  baseScale = 1,
  cropXPercent = 0,
  cropYPercent = 0,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 後方互換: motionType 未指定で kenBurns=true の場合は zoom_in とみなす
  const effectiveMotion: CameraMotionType = motionProfile === "still"
    ? "static"
    : motionType ?? (kenBurns ? "zoom_in" : "static");

  const motionProgress = durationInFrames > 1
    ? interpolate(frame, [0, durationInFrames - 1], [0, 1], {
      easing: Easing.inOut(Easing.ease),
      extrapolateRight: "clamp",
    })
    : 0;

  const profileSettings = (() => {
    switch (motionProfile) {
      case "gentle":
        return { panAmount: 1.35, zoomMultiplier: 0.35, shakeAmplitude: 0.25 };
      case "still":
        return { panAmount: 0, zoomMultiplier: 0, shakeAmplitude: 0 };
      case "standard":
      default:
        return { panAmount: 4, zoomMultiplier: 1, shakeAmplitude: 1.2 };
    }
  })();

  const configuredZoomDelta = Math.abs(zoomEnd - zoomStart);
  const baseZoomDelta = configuredZoomDelta > 0 ? configuredZoomDelta : 0.08;
  const panAmount = profileSettings.panAmount * motionIntensity;
  const zoomAmount = baseZoomDelta * profileSettings.zoomMultiplier * motionIntensity;

  let scale  = 1;
  let transX = 0; // %
  let transY = 0; // %

  switch (effectiveMotion) {
    case "zoom_in":
      scale = interpolate(motionProgress, [0, 1], [zoomStart, zoomStart + zoomAmount]);
      break;

    case "zoom_out":
      scale = interpolate(motionProgress, [0, 1], [zoomStart + zoomAmount, zoomStart]);
      break;

    case "pan_right":
      scale = 1 + zoomAmount * 0.5; // 少しズームして余白を作る
      transX = interpolate(motionProgress, [0, 1], [-panAmount, panAmount]);
      break;

    case "pan_left":
      scale = 1 + zoomAmount * 0.5;
      transX = interpolate(motionProgress, [0, 1], [panAmount, -panAmount]);
      break;

    case "tilt_up":
      scale = 1 + zoomAmount * 0.5;
      transY = interpolate(motionProgress, [0, 1], [panAmount, -panAmount]);
      break;

    case "tilt_down":
      scale = 1 + zoomAmount * 0.5;
      transY = interpolate(motionProgress, [0, 1], [-panAmount, panAmount]);
      break;

    case "shake": {
      if (motionProfile === "gentle") {
        // gentle はシェイクではなく、ほぼ静止に近い低速ドリフトに落とす
        const amp = profileSettings.shakeAmplitude * motionIntensity;
        transX = Math.sin(frame * 0.05) * amp;
        transY = Math.sin(frame * 0.04 + 1.2) * amp * 0.6;
        scale = 1 + zoomAmount * 0.2;
      } else {
        // 高周波の微振動（sin波の重ね合わせ）
        const amp = profileSettings.shakeAmplitude * motionIntensity;
        transX = Math.sin(frame * 0.9) * amp + Math.sin(frame * 1.7) * amp * 0.5;
        transY = Math.sin(frame * 1.1) * amp * 0.6 + Math.sin(frame * 2.3) * amp * 0.3;
        scale = 1 + zoomAmount * 0.3;
      }
      break;
    }

    case "static":
    default:
      scale = 1;
      break;
  }

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `translate(${transX}%, ${transY}%)` }}>
        <Img
          src={src}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: `${50 + cropXPercent}% ${50 + cropYPercent}%`,
            transform: `scale(${baseScale * scale})`,
            transformOrigin: `${originX * 100}% ${originY * 100}%`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
