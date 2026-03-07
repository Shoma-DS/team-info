import React from "react";
import { AbsoluteFill, OffthreadVideo, useVideoConfig } from "remotion";
import { CutSegment } from "../types";

interface SceneProps {
  videoSrc: string;
  cut: CutSegment;
  brightness?: number;   // 0-2 (1=normal)
  saturation?: number;   // 0-2 (1=normal)
}

export const Scene: React.FC<SceneProps> = ({
  videoSrc,
  cut,
  brightness = 1,
  saturation = 1,
}) => {
  const { fps } = useVideoConfig();
  const startFrom = Math.round(cut.start * fps);

  return (
    <AbsoluteFill>
      <OffthreadVideo
        src={videoSrc}
        startFrom={startFrom}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          filter: `brightness(${brightness}) saturate(${saturation})`,
        }}
      />
    </AbsoluteFill>
  );
};
