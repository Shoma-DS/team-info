import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

type HookType = "question" | "statement" | "visual" | "unknown";
const HOOK_FONT_FAMILY =
  '"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", sans-serif';
// 白→黄→白→黄 の交互配色（参考動画に合わせた標準パターン）
const HOOK_LINE_COLORS = ["#ffffff", "#f4d56f", "#ffffff", "#f4d56f"];

interface HookProps {
  hookType: HookType;
  text?: string;
  durationFrames?: number;
  startFrame?: number;
  endFrame?: number;
}

/** 最初の3秒に表示するフック演出コンポーネント */
export const Hook: React.FC<HookProps> = ({
  hookType,
  text,
  durationFrames = 90,
  startFrame = 0,
  endFrame,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const effectiveEndFrame = endFrame ?? durationFrames;

  if (frame < startFrame || frame >= effectiveEndFrame) return null;

  const localFrame = frame - startFrame;
  const localDuration = Math.max(1, effectiveEndFrame - startFrame);

  const fadeIn = interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(localFrame, [localDuration - 15, localDuration], [1, 0], {
    extrapolateLeft: "clamp",
  });
  const opacity = Math.min(fadeIn, fadeOut);

  const bounce = spring({ fps, frame: localFrame, config: { damping: 10, stiffness: 200 } });
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
  const lines = text.split("\n");

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
        opacity,
        paddingTop: "18%",
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          textAlign: "center",
          maxWidth: "82%",
        }}
      >
        {lines.map((line, index) => (
          <div
            key={`${line}-${index}`}
            style={{
              fontFamily: HOOK_FONT_FAMILY,
              fontSize: 76,
              fontWeight: 900,
              color: HOOK_LINE_COLORS[index] ?? "#ffffff",
              lineHeight: 1.02,
              letterSpacing: "0.01em",
              // 縁取りは細くして色が見えるようにする。
              // paint-order: stroke fill で塗り順を「縁→塗り」にするとより効果的だが
              // ReactのCSSプロパティ型に含まれないため textShadow で代替。
              WebkitTextStroke: "3px #000000",
              textShadow: [
                "0 0 4px #000",
                "0 0 4px #000",
                "0 5px 0 rgba(0,0,0,0.35)",
                "0 10px 18px rgba(0,0,0,0.3)",
              ].join(", "),
              marginTop: index === 0 ? 0 : -6,
            }}
          >
            {line}
          </div>
        ))}
        {isQuestion && (
          <div
            style={{
              fontFamily: HOOK_FONT_FAMILY,
              fontSize: 70,
              fontWeight: 900,
              color: "#ffffff",
              WebkitTextStroke: "5px #000000",
              marginTop: 4,
            }}
          >
            ❓
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
