import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { splitDisplayLines } from "../../textLayout";

type HookType = "question" | "statement" | "visual" | "unknown";
const HOOK_FONT_FAMILY =
  '"Noto Sans JP", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif';
// 白→黄→白→黄 の交互配色（参考動画に合わせた標準パターン）
const HOOK_LINE_COLORS = ["#ffffff", "#f4d56f", "#ffffff", "#f4d56f"];

interface HookProps {
  hookType: HookType;
  text?: string;
  durationFrames?: number;
  startFrame?: number;
  endFrame?: number;
  /** フォントファミリーを上書き（省略時は HOOK_FONT_FAMILY） */
  fontFamily?: string;
  /** 行ごとの文字色を上書き（省略時は HOOK_LINE_COLORS） */
  lineColors?: string[];
  /** 文字サイズを上書き（省略時は 120） */
  fontSize?: number;
  /** 内枠（黒）の幅を上書き（省略時は "6px"） */
  strokeWidth?: string;
  /** 縁取り色を上書き（省略時は黒） */
  strokeColor?: string;
  /** 外枠（白）の幅を上書き（省略時は "20px"） */
  outerStrokeWidth?: string;
  /** ドロップシャドウを上書き */
  textShadow?: string;
  /** フック全体の上部余白（縦位置調整）。省略時は "18%" */
  paddingTop?: string;
  /** 縦方向の配置位置。省略時は "center" */
  justifyContent?: "center" | "flex-start" | "flex-end";
  /** テキストの最大幅。省略時は "95%" */
  maxWidth?: string;
}



/** 最初の3秒に表示するフック演出コンポーネント */
export const Hook: React.FC<HookProps> = ({
  hookType,
  text,
  durationFrames = 90,
  startFrame = 0,
  endFrame,
  fontFamily,
  lineColors,
  fontSize = 120,
  strokeWidth = "6px",
  strokeColor = "#000000",
  outerStrokeWidth = "20px",
  textShadow,
  paddingTop = "18%",
  justifyContent = "center",
  maxWidth = "95%",
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
  const lines = splitDisplayLines(text, {
    maxCharsPerLine: 20,
    preserveExistingLineBreaks: true,
  });

  const resolvedFontFamily = fontFamily ?? HOOK_FONT_FAMILY;
  const resolvedLineColors = lineColors ?? HOOK_LINE_COLORS;
  const resolvedTextShadow = textShadow ?? [
    "0 0 4px #000",
    "0 0 4px #000",
    "0 5px 0 rgba(0,0,0,0.65)",
    "0 10px 18px rgba(0,0,0,0.55)",
  ].join(", ");

  return (
    <AbsoluteFill
      style={{
        justifyContent,
        alignItems: "center",
        pointerEvents: "none",
        opacity,
        paddingTop,
      }}
    >

      <div
        style={{
          transform: `scale(${scale})`,
          textAlign: "center",
          maxWidth,
        }}
      >

        {lines.map((line, index) => {
          const sharedStyle = {
            fontFamily: resolvedFontFamily,
            fontSize,
            fontWeight: 900 as const,
            lineHeight: 1.1,
            letterSpacing: "0.01em",
          };
          return (
            <div key={`${line}-${index}`} style={{ position: "relative", marginTop: index === 0 ? 0 : 4 }}>
              {/* 外枠レイヤー: 白い太いストローク + ドロップシャドウ */}
              <div style={{
                ...sharedStyle,
                color: "#ffffff",
                WebkitTextStroke: `${outerStrokeWidth} #ffffff`,
                textShadow: resolvedTextShadow,
              }}>
                {line}
              </div>
              {/* 内枠レイヤー: 黒ストローク + 文字色 */}
              <div style={{
                ...sharedStyle,
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                textAlign: "center",
                color: resolvedLineColors[index] ?? "#ffffff",
                WebkitTextStroke: `${strokeWidth} ${strokeColor}`,
              }}>
                {line}
              </div>
            </div>
          );
        })}
        {isQuestion && (
          <div
            style={{
              fontFamily: resolvedFontFamily,
              fontSize: Math.round(fontSize * 0.92),
              fontWeight: 900,
              color: "#ffffff",
              WebkitTextStroke: `${Math.max(3, Math.round(parseFloat(strokeWidth) * 0.625))}px ${strokeColor}`,
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
