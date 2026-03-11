import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface SubtitleProps {
  text: string;
  fontSize?: number;
  color?: string;
  bgColor?: string;
  yPercent?: number;        // 上からの % (0-100)
  platform?: "tiktok" | "shorts" | "reels";
}

export const Subtitle: React.FC<SubtitleProps> = ({
  text,
  fontSize = 52,
  color = "#ffffff",
  bgColor = "rgba(0,0,0,0.55)",
  yPercent = 75,
  platform = "tiktok",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // フェードイン + ポップアニメーション
  const progress = spring({ fps, frame, config: { damping: 14, stiffness: 180 } });
  const opacity = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(progress, [0, 1], [0.88, 1]);

  const fontWeight = platform === "tiktok" ? "900" : platform === "reels" ? "400" : "700";
  const letterSpacing = platform === "reels" ? "0.04em" : "0.01em";

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: `${yPercent}%`,
          left: "50%",
          transform: `translateX(-50%) scale(${scale})`,
          opacity,
          maxWidth: "88%",
          textAlign: "center",
        }}
      >
        <span
          style={{
            display: "inline-block",
            fontSize,
            fontWeight,
            color,
            letterSpacing,
            lineHeight: 1.35,
            padding: "0.18em 0.6em",
            borderRadius: 10,
            background: bgColor,
            textShadow: "0 2px 8px rgba(0,0,0,0.5)",
          }}
        >
          {text}
        </span>
      </div>
    </AbsoluteFill>
  );
};
