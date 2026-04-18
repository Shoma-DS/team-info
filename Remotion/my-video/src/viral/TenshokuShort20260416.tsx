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
import { Hook } from "./components/Hook";
import { SectionLayout } from "./components/SectionLayout";

import { SUBTITLE_TIMELINE } from "./generated/TenshokuShort20260416Subtitles";
import { VIRAL_ADULT_AFFILIATE_FONT_FAMILY } from "./fonts";
import { splitDisplayLines } from "../textLayout";

const TITLE = "JobChangeShort_20260416";
const TEXT_COLOR = "#ffffff";

const STROKE_COLOR = "#000000";
const OUTER_STROKE_COLOR = "#ffffff";
const DROP_SHADOW = "0 4px 0 rgba(0,0,0,0.1), 0 8px 15px rgba(0,0,0,0.1)";

const SUBTITLE_STYLE = {
  yPercent: 78,
  fontSize: 90,
  fontWeight: "900" as const,
  color: TEXT_COLOR,
  strokeWidth: "0px",
  strokeColor: STROKE_COLOR,
  fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
};

<<<<<<< HEAD
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
=======
const HOOK_LINE_COLORS = ["#ffffff", "#f4d56f", "#ffffff"];
>>>>>>> 02187965 (転職ショート動画のレイアウト最適化とイラスト変更)

const SubtitleTrack: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  // hook の間は字幕を出さない（Hookコンポーネントが担当するため）
  const hookEndFrame = SUBTITLE_TIMELINE.find(s => s.from > 0)?.from ?? 173;
  if (frame < hookEndFrame) return null;


  const entry = SUBTITLE_TIMELINE.find((s) => frame >= s.from && frame < s.to);
  if (!entry) return null;

  const relFrame = frame - entry.from;
  const progress = spring({ fps, frame: relFrame, config: { damping: 14, stiffness: 180 } });
  const scale = interpolate(progress, [0, 1], [0.9, 1]);
  const opacity = interpolate(relFrame, [0, 5], [0, 1]);

  const lines = splitDisplayLines(entry.text, { maxCharsPerLine: 16 });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{
        position: "absolute",
        top: `${SUBTITLE_STYLE.yPercent}%`,
        left: "50%",
        transform: `translateX(-50%) scale(${scale})`,
        opacity,
        width: "95%",
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
            lineHeight: 1.25
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
  const totalFrames = 1650;
  const hookText = SUBTITLE_TIMELINE[0]?.text ?? "";

  return (
    <AbsoluteFill style={{ background: "#FAFAFA" }}>
      <Sequence name="背景" durationInFrames={totalFrames}>
        <ImageScene
          src={staticFile("viral/転職ショート_20260416/background.png")}
          motionType="zoom_in"
          motionProfile="gentle"
          motionIntensity={0.3}
        />
      </Sequence>

      <Sequence name="フック" from={0} durationInFrames={173}>
        {/* イラスト（下部配置） */}
        <div
          style={{
            position: "absolute",
            bottom: "10%",
            height: "50%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <img
            src={staticFile("viral/転職ショート_20260416/hook.png")}
            style={{ 
              maxHeight: "100%",
              maxWidth: "90%",
              objectFit: "contain",
              filter: "drop-shadow(0 15px 25px rgba(0,0,0,0.1))"
            }}
          />
        </div>

        {/* タイトル名（上部配置） */}
        <div style={{ position: "absolute", top: 0, width: "100%", zIndex: 10 }}>
          <Hook
            hookType="statement"
            text={"優秀な人が黙って去る会社\nの特徴3選"}
            fontFamily={SUBTITLE_STYLE.fontFamily}
            fontSize={110}
            lineColors={["#e53935", "#2c3e50"]}
            strokeWidth="0"
            paddingTop="15%"
            startFrame={0}
            durationFrames={173}
          />
        </div>
      </Sequence>
      
      <Sequence name="セクション1" from={173} durationInFrames={625 - 173}>
        <SectionLayout 
          title="① 現場の意見が完全スルーされる" 
          imageSrc={staticFile("viral/転職ショート_20260416/s1.png")} 
        />
      </Sequence>

      <Sequence name="セクション2" from={625} durationInFrames={1043 - 625}>
        <SectionLayout 
          title="② 頑張った分だけ損をする評価" 
          imageSrc={staticFile("viral/転職ショート_20260416/s2.png")} 
        />
      </Sequence>

      <Sequence name="セクション3" from={1043} durationInFrames={1454 - 1043}>
        <SectionLayout 
          title="③ 尊敬できる上司が一人もいない" 
          imageSrc={staticFile("viral/転職ショート_20260416/s3.png")} 
        />
      </Sequence>

      <Sequence name="CTA" from={1454} durationInFrames={totalFrames - 1454}>
        <ImageScene
           src={staticFile("viral/転職ショート_20260416/cta.png")}
           motionType="zoom_in"
        />

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
