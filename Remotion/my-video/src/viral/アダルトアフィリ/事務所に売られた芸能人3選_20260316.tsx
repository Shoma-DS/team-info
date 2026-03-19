/**
 * ViralVideo.tsx — 事務所に売られた芸能人3選
 * 生成日: 2026-03-16 | プラットフォーム: tiktok | 尺: 51.7秒 / 1550フレーム
 * スピーカー: 青山龍星 / ノーマル (VOICEVOX)
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
import { ImageScene } from "../components/ImageScene";
import { Hook } from "../components/Hook";
import {
  useViralAdultAffiliateFont,
  VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
} from "../fonts";
import { SUBTITLE_TIMELINE } from "../generated/事務所に売られた芸能人3選";

const TITLE = "事務所に売られた芸能人3選";
const TEXT_COLOR = "#ffffff";
const STROKE_COLOR = "#000000";
const OUTER_STROKE = "20px";
const OUTER_STROKE_COLOR = "#ffffff";
const DROP_SHADOW = "0 4px 0 rgba(0,0,0,0.85), 0 8px 20px rgba(0,0,0,0.65)";

const SUBTITLE_STYLE = {
  yPercent: 55,
  fontSize: 140,
  fontWeight: "900" as const,
  color: TEXT_COLOR,
  background: undefined,
  paddingH: 0,
  paddingV: 0,
  borderRadius: 0,
  strokeWidth: "1.5px",
  strokeColor: STROKE_COLOR,
  fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
};

const HOOK_LINE_COLORS = ["#f4d56f", "#f4a898", "#f0c8d8", "#ffffff"];
const NAME_COLOR = "#FFE400";
const NAME_COLORS = [NAME_COLOR, NAME_COLOR];

const getLineColors = (text: string, from: number): string[] => {
  const lines = text.split("\n");
  const isNameCard = /^[1-3]\./.test(text.trim());
  if (isNameCard) {
    return lines.map((_, i) => NAME_COLORS[i] ?? "#ffffff");
  }
  if (from < 52) {
    return lines.map((_, i) => HOOK_LINE_COLORS[i] ?? HOOK_LINE_COLORS[0]);
  }
  return lines.map(() => SUBTITLE_STYLE.color);
};

const FADE_FRAMES = 12;
const SCENE_TIMELINE: {
  from: number; to: number; src: string;
  motionType?: string; motionIntensity?: number;
  motionProfile?: "standard" | "gentle" | "still";
  originX?: number; originY?: number;
}[] = [
  // hook
  { from: 0,    to: 62,   src: staticFile(`viral/${TITLE}/materials/00_hook.jpg`),   motionType: "zoom_in",  motionProfile: "gentle", motionIntensity: 0.5, originX: 0.5, originY: 0.4 },
  // s1: 清水富美加
  { from: 62,   to: 206,  src: staticFile(`viral/${TITLE}/materials/01_s1_1.jpg`),   motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
  { from: 206,  to: 350,  src: staticFile(`viral/${TITLE}/materials/01_s1_2.jpg`),   motionType: "pan_right",motionProfile: "gentle", motionIntensity: 0.4, originX: 0.4, originY: 0.5 },
  { from: 350,  to: 494,  src: staticFile(`viral/${TITLE}/materials/01_s1_3.jpg`),   motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
  // s2: 能年玲奈
  { from: 494,  to: 652,  src: staticFile(`viral/${TITLE}/materials/02_s2_1.jpg`),   motionType: "zoom_in",  motionProfile: "gentle", motionIntensity: 0.4, originX: 0.5, originY: 0.4 },
  { from: 652,  to: 810,  src: staticFile(`viral/${TITLE}/materials/02_s2_2.jpg`),   motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
  { from: 810,  to: 969,  src: staticFile(`viral/${TITLE}/materials/02_s2_3.jpg`),   motionType: "pan_left", motionProfile: "gentle", motionIntensity: 0.4, originX: 0.6, originY: 0.5 },
  // s3: 飯島直子
  { from: 969,  to: 1106, src: staticFile(`viral/${TITLE}/materials/03_s3_1.jpg`),   motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
  { from: 1106, to: 1243, src: staticFile(`viral/${TITLE}/materials/03_s3_2.jpg`),   motionType: "zoom_out", motionProfile: "gentle", motionIntensity: 0.4, originX: 0.5, originY: 0.4 },
  { from: 1243, to: 1379, src: staticFile(`viral/${TITLE}/materials/03_s3_3.jpg`),   motionType: "pan_right",motionProfile: "gentle", motionIntensity: 0.4, originX: 0.4, originY: 0.5 },
  // CTA
  { from: 1379, to: 1550, src: staticFile(`viral/${TITLE}/materials/99_cta.jpg`),    motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
];

const INTERRUPT_FRAMES: number[] = [62, 494, 969];

const SceneImage: React.FC<{ entry: typeof SCENE_TIMELINE[0] }> = ({ entry }) => (
  <ImageScene
    src={entry.src}
    motionType={(entry.motionType as "zoom_in" | "zoom_out" | "pan_right" | "pan_left" | "tilt_up" | "tilt_down" | "shake" | "static") ?? "static"}
    motionProfile={entry.motionProfile ?? "still"}
    motionIntensity={entry.motionIntensity ?? 0}
    originX={entry.originX ?? 0.5}
    originY={entry.originY ?? 0.5}
  />
);

const ImageSceneTrack: React.FC = () => {
  const frame = useCurrentFrame();
  const idx = SCENE_TIMELINE.findIndex((s) => frame >= s.from && frame < s.to);
  const current = idx >= 0 ? SCENE_TIMELINE[idx] : SCENE_TIMELINE[SCENE_TIMELINE.length - 1];
  const prev = idx > 0 ? SCENE_TIMELINE[idx - 1] : null;

  const relFrame = idx >= 0 ? frame - current.from : 0;
  const isFading = prev !== null && relFrame < FADE_FRAMES;
  const fadeOpacity = isFading ? relFrame / FADE_FRAMES : 1;

  return (
    <AbsoluteFill>
      {isFading && (
        <AbsoluteFill style={{ opacity: 1 - fadeOpacity }}>
          <SceneImage entry={prev!} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ opacity: fadeOpacity }}>
        <SceneImage entry={current} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const SubtitleTrack: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const hookOverlayEndFrames = SUBTITLE_TIMELINE[0]?.to ?? Math.round(3 * fps);
  if (frame < hookOverlayEndFrames) return null;

  const entry = SUBTITLE_TIMELINE.find((s) => frame >= s.from && frame < s.to);
  if (!entry) return null;

  const relFrame = frame - entry.from;
  const progress = spring({ fps, frame: relFrame, config: { damping: 14, stiffness: 180 } });
  const opacity = interpolate(relFrame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(progress, [0, 1], [0.88, 1]);
  const lines = entry.text.split("\n");
  const lineColors = getLineColors(entry.text, entry.from);
  const isNameCard = /^[1-3]\./.test(entry.text.trim());

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: `${SUBTITLE_STYLE.yPercent}%`,
          left: "50%",
          transform: `translateX(-50%) scale(${scale})`,
          opacity,
          width: "100%",
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
          {lines.map((line, index) => {
            const fs = isNameCard ? 170 : SUBTITLE_STYLE.fontSize;
            const outerStroke = isNameCard ? "22px" : OUTER_STROKE;
            const sharedStyle = {
              fontFamily: SUBTITLE_STYLE.fontFamily,
              fontSize: fs,
              fontWeight: SUBTITLE_STYLE.fontWeight,
              lineHeight: 1.1,
              whiteSpace: "pre-wrap" as const,
            };
            return (
              <div
                key={`${entry.from}-${index}-${line}`}
                style={{ position: "relative", marginTop: index === 0 ? 0 : 12 }}
              >
                <div style={{
                  ...sharedStyle,
                  color: OUTER_STROKE_COLOR,
                  WebkitTextStroke: `${outerStroke} ${OUTER_STROKE_COLOR}`,
                  textShadow: DROP_SHADOW,
                }}>
                  {line}
                </div>
                <div style={{
                  ...sharedStyle,
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "100%",
                  textAlign: "center",
                  color: lineColors[index] ?? SUBTITLE_STYLE.color,
                  WebkitTextStroke: `${SUBTITLE_STYLE.strokeWidth} ${SUBTITLE_STYLE.strokeColor}`,
                }}>
                  {line}
                </div>
              </div>
            );
          })}
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

export const ViralVideoJimusho: React.FC = () => {
  useViralAdultAffiliateFont();
  const { fps } = useVideoConfig();
  const totalFrames = 1550;
  const hookTextStartFrame = SUBTITLE_TIMELINE[0]?.from ?? 0;
  const hookOverlayEndFrames = SUBTITLE_TIMELINE[0]?.to ?? Math.round(3 * fps);
  const hookText = SUBTITLE_TIMELINE[0]?.text ?? ""; // card モードで確定した改行をそのまま使う

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence name="背景画像" durationInFrames={totalFrames}>
        <ImageSceneTrack />
      </Sequence>
      <Sequence name="フック テキスト" durationInFrames={hookOverlayEndFrames}>
        <Hook
          hookType="statement"
          text={hookText}
          startFrame={hookTextStartFrame}
          endFrame={hookOverlayEndFrames}
          durationFrames={hookOverlayEndFrames}
          fontFamily={VIRAL_ADULT_AFFILIATE_FONT_FAMILY}
          fontSize={160}
          strokeWidth="1.5px"
          strokeColor={STROKE_COLOR}
          textShadow={DROP_SHADOW}
          lineColors={HOOK_LINE_COLORS}
          paddingTop="65%"
        />
      </Sequence>
      <Sequence name="フラッシュ 演出" durationInFrames={totalFrames}>
        <FlashTrack />
      </Sequence>
      <Sequence name="字幕" durationInFrames={totalFrames}>
        <SubtitleTrack />
      </Sequence>
      <Sequence name="音声 ナレーション" durationInFrames={totalFrames}>
        <Audio src={staticFile(`viral/${TITLE}/audio/narration.wav`)} volume={1.0} />
      </Sequence>
    </AbsoluteFill>
  );
};
