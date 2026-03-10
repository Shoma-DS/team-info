import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

interface ImageSceneProps {
  src: string;
  kenBurns?: boolean;   // Ken Burns エフェクト（ゆるやかなズーム）
  zoomStart?: number;   // 開始倍率
  zoomEnd?: number;     // 終了倍率
  originX?: number;     // ズーム中心 X (0-1)
  originY?: number;     // ズーム中心 Y (0-1)
}

export const ImageScene: React.FC<ImageSceneProps> = ({
  src,
  kenBurns = true,
  zoomStart = 1.0,
  zoomEnd = 1.07,
  originX = 0.5,
  originY = 0.4,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const scale = kenBurns
    ? interpolate(frame, [0, durationInFrames], [zoomStart, zoomEnd], {
        extrapolateRight: "clamp",
      })
    : 1;

  return (
    <AbsoluteFill>
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
          transformOrigin: `${originX * 100}% ${originY * 100}%`,
        }}
      />
    </AbsoluteFill>
  );
};
