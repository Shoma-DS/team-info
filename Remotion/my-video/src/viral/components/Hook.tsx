import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

type HookType = "question" | "statement" | "visual" | "unknown";

interface HookProps {
  hookType: HookType;
  text?: string;
  durationFrames?: number;
}

/** 最初の3秒に表示するフック演出コンポーネント */
export const Hook: React.FC<HookProps> = ({ hookType, text, durationFrames = 90 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationFrames - 15, durationFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });
  const opacity = Math.min(fadeIn, fadeOut);

  const bounce = spring({ fps, frame, config: { damping: 10, stiffness: 200 } });
  const scale = interpolate(bounce, [0, 1], [0.7, 1]);

  if (hookType === "visual") {
    // 視覚フック: ズームフラッシュ
    const flashOpacity = interpolate(frame, [0, 4, 8], [1, 0.3, 0], {
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill
        style={{
          background: "white",
          opacity: flashOpacity,
          pointerEvents: "none",
        }}
      />
    );
  }

  if (!text) return null;

  const isQuestion = hookType === "question";

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
        opacity,
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          textAlign: "center",
          padding: "24px 48px",
          borderRadius: 20,
          background: isQuestion
            ? "linear-gradient(135deg, #ff6b35, #ff3c78)"
            : "linear-gradient(135deg, #1a1a2e, #16213e)",
          boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
          maxWidth: "80%",
        }}
      >
        <div
          style={{
            fontSize: 60,
            fontWeight: 900,
            color: "#ffffff",
            lineHeight: 1.3,
            textShadow: "0 2px 12px rgba(0,0,0,0.4)",
            letterSpacing: "0.02em",
          }}
        >
          {text}
          {isQuestion && (
            <span style={{ display: "block", fontSize: 72, marginTop: 4 }}>❓</span>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
