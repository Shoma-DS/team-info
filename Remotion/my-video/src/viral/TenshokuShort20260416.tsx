/**
 * TenshokuShort20260416.tsx — 【そりゃ辞めるわ】優秀な人が黙って去る会社の特徴3選
 * 生成日: 2026-04-16 | 尺: 79.8秒
 */
import React from "react";
import {
  AbsoluteFill,
  Sequence,
  staticFile,
  useVideoConfig,
  useCurrentFrame,
  interpolate,
  spring,
  Audio,
} from "remotion";
import { Hook } from "./components/Hook";
import { SectionLayout } from "./components/SectionLayout";
import { ImageScene } from "./components/ImageScene";
import { SUBTITLE_TIMELINE } from "./generated/TenshokuShort20260416Subtitles";
import { VIRAL_ADULT_AFFILIATE_FONT_FAMILY } from "./fonts";

const TEXT_COLOR = "#FFFFFF";
const STROKE_COLOR = "#000000";

const SUBTITLE_STYLE = {
  fontSize: 95,

  fontWeight: "900" as const,
  color: "#000000",
  fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
};

const SubtitleTrack: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const entry = SUBTITLE_TIMELINE.find((s) => frame >= s.from && frame < s.to);
  if (!entry) return null;

  if (entry.text === "") return null;

  const currentDuration = entry.to - entry.from;
  const progressInSegment = frame - entry.from;

  const fadeInFrames = 3;
  const fadeOutFrames = 3;
  const opacity = interpolate(
    progressInSegment,
    [0, fadeInFrames, currentDuration - fadeOutFrames, currentDuration],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: "5%",
        opacity,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          ...SUBTITLE_STYLE,
          textAlign: "center",
          maxWidth: "95%",
          whiteSpace: "pre-wrap",
          lineHeight: 1.2,
        }}
      >
        {entry.text}
      </div>
    </AbsoluteFill>
  );
};


export const TenshokuShort20260416: React.FC = () => {
  const totalFrames = 2394;

  return (
    <AbsoluteFill style={{ background: "#FAFAFA" }}>
      <Sequence name="フック" from={0} durationInFrames={240}>
        {/* イラスト（最下部配置） */}
        <div
          style={{
            position: "absolute",
            bottom: "8%",
            height: "45%",
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
              filter: "drop-shadow(0 10px 20px rgba(0,0,0,0.08))"
            }}
          />
        </div>

        {/* タイトル名（最上部配置） */}
        <div style={{ position: "absolute", top: 0, width: "100%", height: "100%", zIndex: 10 }}>
          <Hook
            hookType="statement"
            text={"優秀な人が黙って去る会社\nの特徴3選"}
            fontFamily={SUBTITLE_STYLE.fontFamily}
            fontSize={135}

            lineColors={["#ff2a2a", "#000000"]}
            strokeWidth="0"
            outerStrokeWidth="0"
            textShadow="none"
            paddingTop="8%"
            justifyContent="flex-start"
            maxWidth="98%"
            startFrame={0}

            durationFrames={240}
          />
        </div>
      </Sequence>
      
      <Sequence name="セクション1" from={240} durationInFrames={905 - 240}>
        <SectionLayout 
          title="① 現場の意見が完全スルーされる" 
          imageSrc={staticFile("viral/転職ショート_20260416/s1.png")} 
          photoSrc={staticFile("viral/転職ショート_20260416/p1.png")}
          switchFrame={330}
        />
      </Sequence>

      <Sequence name="セクション2" from={905} durationInFrames={1510 - 905}>
        <SectionLayout 
          title="② 頑張った分だけ損をする評価" 
          imageSrc={staticFile("viral/転職ショート_20260416/s2.png")} 
          photoSrc={staticFile("viral/転職ショート_20260416/p2.png")}
          switchFrame={300}
        />
      </Sequence>

      <Sequence name="セクション3" from={1510} durationInFrames={2110 - 1510}>
        <SectionLayout 
          title="③ 尊敬できる上司が一人もいない" 
          imageSrc={staticFile("viral/転職ショート_20260416/s3.png")} 
          photoSrc={staticFile("viral/転職ショート_20260416/p3.png")}
          switchFrame={300}
        />
      </Sequence>

      <Sequence name="CTA" from={2110} durationInFrames={2394 - 2110}>
        <AbsoluteFill style={{ backgroundColor: "white" }}>
          {/* 画像エリア: 字幕と被らないよう上部に寄せる */}
          <div style={{ position: "absolute", top: "15%", height: "55%", width: "100%" }}>
            <ImageScene
              src={staticFile(
                useCurrentFrame() >= 138 
                  ? "viral/転職ショート_20260416/cta_alt.png" 
                  : "viral/転職ショート_20260416/cta.png"
              )}
              motionType="zoom_in"
              motionProfile="gentle"
              motionIntensity={0.2}
            />
          </div>
        </AbsoluteFill>
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
