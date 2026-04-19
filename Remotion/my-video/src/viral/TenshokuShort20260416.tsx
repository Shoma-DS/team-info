/**
 * TenshokuShort20260416.tsx — 【そりゃ辞めるわ】優秀な人が黙って去る会社の特徴3選
 * 生成日: 2026-04-16 | 尺: 56.5秒
 */
import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ImageScene } from "./components/ImageScene";
import { SUBTITLE_TIMELINE } from "./generated/TenshokuShort20260416Subtitles";
import { VIRAL_ADULT_AFFILIATE_FONT_FAMILY } from "./fonts";
import { splitDisplayLines } from "../textLayout";

const TEXT_COLOR = "#ffffff";
const STROKE_COLOR = "#000000";
const OUTER_STROKE_COLOR = "#ffffff";
const DROP_SHADOW = "0 4px 0 rgba(0,0,0,0.85), 0 8px 20px rgba(0,0,0,0.65)";

const SUBTITLE_STYLE = {
  yPercent: 65,
  fontSize: 100,
  fontWeight: "900" as const,
  color: TEXT_COLOR,
  strokeWidth: "1.5px",
  strokeColor: STROKE_COLOR,
  fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
};

// フック終端フレーム（最初の字幕 from=3 の直前テロップ行が 170 まで続くため）
const HOOK_END_FRAME = 170;

/** 白背景 + いらすとやイラスト + 太字タイトルのフックカード */
const WhiteCardHook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame >= HOOK_END_FRAME) return null;

  const fadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [HOOK_END_FRAME - 15, HOOK_END_FRAME], [1, 0], {
    extrapolateLeft: "clamp",
  });
  const opacity = Math.min(fadeIn, fadeOut);

  const bounce = spring({ fps, frame, config: { damping: 12, stiffness: 180 } });
  const scale = interpolate(bounce, [0, 1], [0.82, 1]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#ffffff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        paddingTop: 280,
        pointerEvents: "none",
        opacity,
      }}
    >
      {/* タイトルテキスト */}
      <div style={{ transform: `scale(${scale})`, textAlign: "center" }}>
        {/* 1行目 */}
        <div
          style={{
            fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
            fontSize: 96,
            fontWeight: 900,
            color: "#1a1a1a",
            lineHeight: 1.25,
            letterSpacing: "0.02em",
          }}
        >
          優秀な人が黙って去る
        </div>
        {/* 2行目: 「3選」だけオレンジ */}
        <div
          style={{
            fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
            fontSize: 96,
            fontWeight: 900,
            color: "#1a1a1a",
            lineHeight: 1.25,
            letterSpacing: "0.02em",
            display: "flex",
            justifyContent: "center",
            alignItems: "baseline",
            gap: 0,
          }}
        >
          会社の特徴
          <span style={{ color: "#ff6600", fontSize: 108 }}>3選</span>
        </div>
      </div>
      {/* いらすとやイラスト */}
      <img
        src={staticFile("viral/転職ショート_20260416/hook_illust.png")}
        style={{
          marginTop: 60,
          height: 700,
          objectFit: "contain",
        }}
      />
    </AbsoluteFill>
  );
};

const SubtitleTrack: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  // フック表示中は字幕を出さない
  if (frame < HOOK_END_FRAME) return null;

  const entry = SUBTITLE_TIMELINE.find((s) => frame >= s.from && frame < s.to);
  if (!entry) return null;

  const relFrame = frame - entry.from;
  const progress = spring({ fps, frame: relFrame, config: { damping: 14, stiffness: 180 } });
  const scale = interpolate(progress, [0, 1], [0.9, 1]);
  const opacity = interpolate(relFrame, [0, 5], [0, 1]);

  const lines = splitDisplayLines(entry.text, { maxCharsPerLine: 14 });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{
        position: "absolute",
        top: `${SUBTITLE_STYLE.yPercent}%`,
        left: "50%",
        transform: `translateX(-50%) scale(${scale})`,
        opacity,
        width: "90%",
        textAlign: "center",
      }}>
        {lines.map((line, idx) => (
          <div key={idx} style={{
            position: "relative",
            fontFamily: SUBTITLE_STYLE.fontFamily,
            fontSize: SUBTITLE_STYLE.fontSize,
            fontWeight: SUBTITLE_STYLE.fontWeight,
            color: SUBTITLE_STYLE.color,
            WebkitTextStroke: `8px ${OUTER_STROKE_COLOR}`,
            textShadow: DROP_SHADOW,
          }}>
            <div style={{
              position: "absolute",
              top: 0, left: 0, width: "100%",
              color: SUBTITLE_STYLE.color,
              WebkitTextStroke: `${SUBTITLE_STYLE.strokeWidth} ${SUBTITLE_STYLE.strokeColor}`,
            }}>{line}</div>
            {line}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

export const TenshokuShort20260416: React.FC = () => {
  const totalFrames = 1733;

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence name="背景" durationInFrames={totalFrames}>
        <ImageScene
          src={staticFile("viral/転職ショート_20260416/background.png")}
          motionType="zoom_in"
          motionProfile="gentle"
          motionIntensity={0.3}
        />
      </Sequence>

      <Sequence name="フック" durationInFrames={HOOK_END_FRAME}>
        <WhiteCardHook />
      </Sequence>

      <Sequence name="字幕" durationInFrames={totalFrames}>
        <SubtitleTrack />
      </Sequence>

      <Sequence name="音声" durationInFrames={totalFrames}>
        <Audio src={staticFile("audio/転職ショート_20260416/narration.wav")} />
      </Sequence>
    </AbsoluteFill>
  );
};
