import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

interface ZoomEffectProps {
  children: React.ReactNode;
  startScale?: number;    // ズーム開始倍率
  endScale?: number;      // ズーム終了倍率
  durationFrames?: number;
  originX?: number;       // ズーム中心 X (0-1)
  originY?: number;       // ズーム中心 Y (0-1)
}

export const ZoomEffect: React.FC<ZoomEffectProps> = ({
  children,
  startScale = 1.0,
  endScale = 1.12,
  durationFrames,
  originX = 0.5,
  originY = 0.5,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const dur = durationFrames ?? durationInFrames;

  const scale = interpolate(frame, [0, dur], [startScale, endScale], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        transformOrigin: `${originX * 100}% ${originY * 100}%`,
        transform: `scale(${scale})`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
