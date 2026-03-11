/**
 * ViralVideo.tsx — 際どいシーンを演じた女性芸能人3選
 * 生成日: 2026-03-11 | プラットフォーム: shorts | 尺: 54秒 / 1620フレーム
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
import { SUBTITLE_TIMELINE } from "./generated/geinoEntameBuzzPatternSubtitles";


// 字幕スタイル (viral_patterns.md: entertainment+high, avg_y=0.532)
const SUBTITLE_STYLE = {
  yPercent: 53,
  fontSize: 58,
  fontWeight: "900" as const,
  color: "#ffffff",
  textShadow: "0 4px 0 rgba(0,0,0,0.24), 0 10px 18px rgba(0,0,0,0.3)",
  letterSpacing: "0.01em",
  strokeWidth: "5px",
  strokeColor: "#000000",
  fontFamily:
    '"Hiragino Maru Gothic ProN", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif',
};
const INTRO_LINE_COLORS = ["#f4d56f", "#ffb1bf", "#f2deff", "#ffffff"];
const NAME_LINE_COLORS = ["#f4d56f", "#ffffff"];

const getLineColors = (text: string, from: number): string[] => {
  const lines = text.split("\n");
  const isIntro = from < 280;
  const isNameCard = /[123]人目は、?/.test(text);

  if (isIntro) {
    return lines.map((_, index) => INTRO_LINE_COLORS[index] ?? "#ffffff");
  }

  if (isNameCard) {
    return lines.map((_, index) => NAME_LINE_COLORS[index] ?? "#ffffff");
  }

  if (lines.length >= 3) {
    return lines.map((_, index) => (index === 0 ? "#fff1ad" : "#ffffff"));
  }

  if (lines.length === 2) {
    return ["#fff1ad", "#ffffff"];
  }

  return ["#fff6de"];
};

// 背景画像タイムライン
const SCENE_TIMELINE: { from: number; to: number; src: string }[] = [
  { from: 0,    to: 90,   src: staticFile("viral/芸能人エンタメ_バズパターン/materials/00_hook.jpg") },
  { from: 90,   to: 270,  src: staticFile("viral/芸能人エンタメ_バズパターン/materials/01_opening.jpg") },
  { from: 270,  to: 390,  src: staticFile("viral/芸能人エンタメ_バズパターン/materials/02_s1_1.jpg") },
  { from: 390,  to: 540,  src: staticFile("viral/芸能人エンタメ_バズパターン/materials/02_s1_2.jpg") },
  { from: 540,  to: 690,  src: staticFile("viral/芸能人エンタメ_バズパターン/materials/02_s1_3.jpg") },
  { from: 690,  to: 840,  src: staticFile("viral/芸能人エンタメ_バズパターン/materials/03_s2_1.jpg") },
  { from: 840,  to: 975,  src: staticFile("viral/芸能人エンタメ_バズパターン/materials/03_s2_2.jpg") },
  { from: 975,  to: 1110, src: staticFile("viral/芸能人エンタメ_バズパターン/materials/03_s2_3.jpg") },
  { from: 1110, to: 1260, src: staticFile("viral/芸能人エンタメ_バズパターン/materials/04_s3_1.png") },
  { from: 1260, to: 1395, src: staticFile("viral/芸能人エンタメ_バズパターン/materials/04_s3_2.png") },
  { from: 1395, to: 1500, src: staticFile("viral/芸能人エンタメ_バズパターン/materials/04_s3_3.png") },
  { from: 1500, to: 1620, src: staticFile("viral/芸能人エンタメ_バズパターン/materials/99_cta.jpg") },
];

// パターンインタラプト (3s=90f, 22s=660f, 37s=1110f, 46s=1380f)
const INTERRUPT_FRAMES: number[] = [90, 660, 1110, 1380];
const SFX_EVENTS = [
  { from: 90, durationInFrames: 18, src: staticFile("viral/芸能人エンタメ_バズパターン/audio/sfx/whoosh.wav"), volume: 0.52 },
  { from: 660, durationInFrames: 18, src: staticFile("viral/芸能人エンタメ_バズパターン/audio/sfx/transition.wav"), volume: 0.5 },
  { from: 1110, durationInFrames: 18, src: staticFile("viral/芸能人エンタメ_バズパターン/audio/sfx/whoosh.wav"), volume: 0.5 },
  { from: 1380, durationInFrames: 15, src: staticFile("viral/芸能人エンタメ_バズパターン/audio/sfx/impact.wav"), volume: 0.58 },
];

const ImageSceneTrack: React.FC = () => {
  const frame = useCurrentFrame();
  const entry =
    SCENE_TIMELINE.find((s) => frame >= s.from && frame < s.to) ??
    SCENE_TIMELINE[SCENE_TIMELINE.length - 1];
  return (
    <AbsoluteFill>
      <ImageScene src={entry.src} kenBurns zoomStart={1.0} zoomEnd={1.07} />
    </AbsoluteFill>
  );
};

const SubtitleTrack: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const hookDurationFrames = Math.round(3 * fps);
  const hookOverlayEndFrames = Math.max(hookDurationFrames, SUBTITLE_TIMELINE[0]?.to ?? hookDurationFrames);
  if (frame < hookOverlayEndFrames) return null; // Hook コンポーネントが担当
  const entry = SUBTITLE_TIMELINE.find((s) => frame >= s.from && frame < s.to);
  if (!entry) return null;

  const relFrame = frame - entry.from;
  const progress = spring({ fps, frame: relFrame, config: { damping: 14, stiffness: 180 } });
  const opacity = interpolate(relFrame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(progress, [0, 1], [0.88, 1]);
  const lines = entry.text.split("\n");
  const lineColors = getLineColors(entry.text, entry.from);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: `${SUBTITLE_STYLE.yPercent}%`,
          left: "50%",
          transform: `translateX(-50%) scale(${scale})`,
          opacity,
          maxWidth: "84%",
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 0,
            textAlign: "center",
          }}
        >
          {lines.map((line, index) => (
            <div
              key={`${entry.from}-${index}-${line}`}
              style={{
                fontFamily: SUBTITLE_STYLE.fontFamily,
                fontSize: index === lines.length - 1 && lines.length >= 3
                  ? SUBTITLE_STYLE.fontSize - 2
                  : SUBTITLE_STYLE.fontSize,
                fontWeight: SUBTITLE_STYLE.fontWeight,
                color: lineColors[index] ?? SUBTITLE_STYLE.color,
                letterSpacing: SUBTITLE_STYLE.letterSpacing,
                lineHeight: 1.02,
                textShadow: SUBTITLE_STYLE.textShadow,
                WebkitTextStroke: `${SUBTITLE_STYLE.strokeWidth} ${SUBTITLE_STYLE.strokeColor}`,
                whiteSpace: "nowrap",
                marginTop: index === 0 ? 0 : -2,
              }}
            >
              {line}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const FlashTrack: React.FC = () => {
  const frame = useCurrentFrame();
  const isFlash = INTERRUPT_FRAMES.some((f) => frame >= f && frame < f + 6);
  if (!isFlash) return null;
  return (
    <AbsoluteFill
      style={{ background: "white", opacity: 0.3, pointerEvents: "none" }}
    />
  );
};

export const ViralVideo: React.FC = () => {
  const { fps } = useVideoConfig();
  const totalFrames = 1620;
  const hookDuration = Math.round(3 * fps);
  const hookTextStartFrame = SUBTITLE_TIMELINE[0]?.from ?? 0;
  const hookOverlayEndFrames = Math.max(hookDuration, SUBTITLE_TIMELINE[0]?.to ?? hookDuration);

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence from={0} durationInFrames={totalFrames}>
        <ImageSceneTrack />
      </Sequence>
      <Sequence from={0} durationInFrames={hookOverlayEndFrames}>
        <Hook
          hookType="statement"
          text={SUBTITLE_TIMELINE[0]?.text ?? ""}
          startFrame={hookTextStartFrame}
          endFrame={hookOverlayEndFrames}
          durationFrames={hookOverlayEndFrames}
        />
      </Sequence>
      <Sequence from={0} durationInFrames={totalFrames}>
        <Audio src={staticFile("viral/芸能人エンタメ_バズパターン/audio/bgm_generated.wav")} volume={0.18} loop />
      </Sequence>
      <Sequence from={0} durationInFrames={totalFrames}>
        <FlashTrack />
      </Sequence>
      <Sequence from={0} durationInFrames={totalFrames}>
        <SubtitleTrack />
      </Sequence>
      {/* ナレーション音源（青山龍星 / VOICEVOX） */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <Audio src={staticFile("viral/芸能人エンタメ_バズパターン/audio/narration.wav")} volume={1.0} />
      </Sequence>
      {SFX_EVENTS.map((event) => (
        <Sequence
          key={`${event.src}-${event.from}`}
          from={event.from}
          durationInFrames={event.durationInFrames}
        >
          <Audio src={event.src} volume={event.volume} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
