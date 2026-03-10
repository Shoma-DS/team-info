/**
 * ViralVideo.tsx — 際どいシーンを演じた女性芸能人3選
 * 生成日: 2026-03-10 | プラットフォーム: shorts | 尺: 54秒 / 1620フレーム
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


// 字幕スタイル (viral_patterns.md: entertainment+high, avg_y=0.524)
const SUBTITLE_STYLE = {
  yPercent: 52,
  fontSize: 53,
  fontWeight: "900" as const,
  color: "#ffffff",
  bgColor: "rgba(0,0,0,0.65)",
  textShadow: "0 2px 12px rgba(0,0,0,0.8), 0 0 4px rgba(0,0,0,1)",
  letterSpacing: "0.02em",
  strokeWidth: "2px",
  strokeColor: "#000000",
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

// 字幕タイムライン (subtitles.json より)
const SUBTITLE_TIMELINE: { from: number; to: number; text: string }[] = [
  { from: 0,    to: 90,   text: "際どいシーンを演じた\n女性芸能人3選！" },
  { from: 90,   to: 180,  text: "清純派なのに…" },
  { from: 180,  to: 270,  text: "あの女優たちが挑んだ衝撃の\n役がこちら。" },
  { from: 270,  to: 360,  text: "1人目は吉高由里子。" },
  { from: 360,  to: 480,  text: "デビュー作『蛇に\nピアス』での演技が業界を\n震わせた。" },
  { from: 480,  to: 585,  text: "ピアスにタトゥー、過激な\n役柄を体当たりで演じ切り、" },
  { from: 585,  to: 690,  text: "清楚なイメージとの\nギャップが大きな話題を\n呼んだ。" },
  { from: 690,  to: 780,  text: "2人目は長澤まさみ。" },
  { from: 780,  to: 900,  text: "天才女優の名にふさわしい\n際どい役への挑戦が続く。" },
  { from: 900,  to: 1005, text: "清純派出身なのに大胆な\n役柄を次々と引き受け、" },
  { from: 1005, to: 1110, text: "女優としての底知れない\n胆力を証明し続けている。" },
  { from: 1110, to: 1200, text: "3人目は深田恭子。" },
  { from: 1200, to: 1305, text: "デビュー当初から\nセクシー路線で人気を博し、" },
  { from: 1305, to: 1395, text: "今なお話題を集め続ける\n圧倒的な存在感。" },
  { from: 1395, to: 1500, text: "このギャップがたまらないと\n今も根強いファンが\n絶えない。" },
  { from: 1500, to: 1620, text: "知らなかった人は\nフォローして教えて！" },
];

// パターンインタラプト (セクション境界: 3s=90f, 20s=600f, 43s=1290f)
const INTERRUPT_FRAMES: number[] = [90, 600, 1290];
const SFX_EVENTS = [
  { from: 90, durationInFrames: 18, src: staticFile("viral/芸能人エンタメ_バズパターン/audio/sfx/whoosh.wav"), volume: 0.52 },
  { from: 600, durationInFrames: 18, src: staticFile("viral/芸能人エンタメ_バズパターン/audio/sfx/transition.wav"), volume: 0.5 },
  { from: 1290, durationInFrames: 15, src: staticFile("viral/芸能人エンタメ_バズパターン/audio/sfx/impact.wav"), volume: 0.58 },
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
  const entry = SUBTITLE_TIMELINE.find((s) => frame >= s.from && frame < s.to);
  if (!entry) return null;

  const relFrame = frame - entry.from;
  const progress = spring({ fps, frame: relFrame, config: { damping: 14, stiffness: 180 } });
  const opacity = interpolate(relFrame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(progress, [0, 1], [0.88, 1]);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: `${SUBTITLE_STYLE.yPercent}%`,
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
            fontSize: SUBTITLE_STYLE.fontSize,
            fontWeight: SUBTITLE_STYLE.fontWeight,
            color: SUBTITLE_STYLE.color,
            letterSpacing: SUBTITLE_STYLE.letterSpacing,
            lineHeight: 1.5,
            padding: "0.18em 0.6em",
            borderRadius: 10,
            background: SUBTITLE_STYLE.bgColor,
            textShadow: SUBTITLE_STYLE.textShadow,
            WebkitTextStroke: `${SUBTITLE_STYLE.strokeWidth} ${SUBTITLE_STYLE.strokeColor}`,
            whiteSpace: "pre-wrap",
            textAlign: "center",
          }}
        >
          {entry.text}
        </span>
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

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence from={0} durationInFrames={totalFrames}>
        <ImageSceneTrack />
      </Sequence>
      <Sequence from={0} durationInFrames={hookDuration}>
        <Hook
          hookType="statement"
          text={(SUBTITLE_TIMELINE[0]?.text ?? "").replace("\n", " ")}
          durationFrames={hookDuration}
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
