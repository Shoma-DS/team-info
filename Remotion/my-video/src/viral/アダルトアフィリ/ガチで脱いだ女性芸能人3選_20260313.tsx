/**
 * ViralVideo.tsx — ガチで脱いだ女性芸能人3選
 * 生成日: 2026-03-13 | プラットフォーム: tiktok | 尺: 62.891秒 / 1887フレーム
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
import { SUBTITLE_TIMELINE } from "../generated/gachiNuida20260313Subtitles";

const TITLE = "ガチで脱いだ女性芸能人3選_20260313";
const RETRO_RED = "#ff5148";
const RETRO_STROKE = "#f5dcc9";
const RETRO_SHADOW = [
  "0 3px 0 rgba(157,43,39,0.96)",
  "0 6px 0 rgba(125,32,29,0.92)",
  "0 12px 18px rgba(83,20,20,0.28)",
].join(", ");

// 字幕スタイル（style_04_crop.jpg 顔のみで戦う芸能人 + style_03_full 女優魂 で照合）
// ストロークのみ・背景ボックスなし（参照: 顔のみ style_04 に合わせた）
// フォント: Mochiy Pop One / 168px / 赤 / クリーム縁 / 赤影 / Y=52%
const SUBTITLE_STYLE = {
  yPercent: 52,  // style_03_full.jpg 実測（テキスト上端 ~52%）
  fontSize: 168,
  fontWeight: "900" as const,
  color: RETRO_RED,
  background: undefined,  // ボックスなし（stroke_entertainment スタイル）
  paddingH: 0,
  paddingV: 0,
  borderRadius: 0,
  strokeWidth: "4px",
  strokeColor: RETRO_STROKE,
  textShadow: RETRO_SHADOW,
  fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
};

// 名前カード（1人目/2人目/3人目）とフックは強調色（黄→ピンク交互）
// フック: 黄 → サーモン → 淡ピンク（video1/2/6 スクショで3色を確認）
const HOOK_LINE_COLORS = [RETRO_RED, RETRO_RED, RETRO_RED];
const NAME_COLORS = [RETRO_RED, RETRO_RED];

const getLineColors = (text: string, from: number): string[] => {
  const lines = text.split("\n");
  const isNameCard = /^[123]人目は/.test(text.trim());
  if (isNameCard) {
    return lines.map((_, i) => NAME_COLORS[i] ?? "#ffffff");
  }
  if (from < 90) {
    return lines.map((_, i) => HOOK_LINE_COLORS[i] ?? HOOK_LINE_COLORS[0]);
  }
  return lines.map(() => SUBTITLE_STYLE.color);
};

// 背景画像タイムライン
const SCENE_TIMELINE: {
  from: number; to: number; src: string;
  motionType?: string; motionIntensity?: number; originX?: number; originY?: number;
}[] = [
  { from: 0,    to: 90,   src: staticFile(`viral/${TITLE}/materials/00_hook.jpg`),   motionType: "zoom_in",  motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
  { from: 90,   to: 258,  src: staticFile(`viral/${TITLE}/materials/02_s1_1.jpg`),  motionType: "shake",    motionIntensity: 1.5, originX: 0.5, originY: 0.5 },
  { from: 258,  to: 462,  src: staticFile(`viral/${TITLE}/materials/02_s1_2.jpg`),  motionType: "zoom_in",  motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
  { from: 462,  to: 586,  src: staticFile(`viral/${TITLE}/materials/02_s1_3.jpg`),  motionType: "pan_right", motionIntensity: 1.2, originX: 0.3, originY: 0.5 },
  { from: 586,  to: 733,  src: staticFile(`viral/${TITLE}/materials/03_s2_1.jpg`),  motionType: "shake",    motionIntensity: 1.5, originX: 0.5, originY: 0.5 },
  { from: 733,  to: 1036, src: staticFile(`viral/${TITLE}/materials/03_s2_2.jpg`),  motionType: "zoom_in",  motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
  { from: 1036, to: 1153, src: staticFile(`viral/${TITLE}/materials/03_s2_3.jpg`),  motionType: "pan_left", motionIntensity: 1.2, originX: 0.7, originY: 0.5 },
  { from: 1153, to: 1333, src: staticFile(`viral/${TITLE}/materials/04_s3_1.jpg`),  motionType: "shake",    motionIntensity: 1.5, originX: 0.5, originY: 0.5 },
  { from: 1333, to: 1481, src: staticFile(`viral/${TITLE}/materials/04_s3_2.jpg`),  motionType: "zoom_out", motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
  { from: 1481, to: 1617, src: staticFile(`viral/${TITLE}/materials/04_s3_3.jpg`),  motionType: "pan_right", motionIntensity: 1.2, originX: 0.3, originY: 0.5 },
  { from: 1617, to: 1887, src: staticFile(`viral/${TITLE}/materials/99_cta.jpg`),   motionType: "zoom_in",  motionIntensity: 0.5, originX: 0.5, originY: 0.5 },
];

// パターンインタラプト（エピソード切り替え: 3s=90f / 19.5s=586f / 38.4s=1153f）
const INTERRUPT_FRAMES: number[] = [90, 586, 1153];

const ImageSceneTrack: React.FC = () => {
  const frame = useCurrentFrame();
  const entry =
    SCENE_TIMELINE.find((s) => frame >= s.from && frame < s.to) ??
    SCENE_TIMELINE[SCENE_TIMELINE.length - 1];
  return (
    <AbsoluteFill>
      <ImageScene
        src={entry.src}
        motionType={
          (entry.motionType as
            | "zoom_in" | "zoom_out" | "pan_right" | "pan_left"
            | "tilt_up" | "tilt_down" | "shake" | "static") ?? "zoom_in"
        }
        motionIntensity={entry.motionIntensity ?? 1.0}
        originX={entry.originX ?? 0.5}
        originY={entry.originY ?? 0.4}
      />
    </AbsoluteFill>
  );
};

const SubtitleTrack: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const hookOverlayEndFrames = Math.max(
    Math.round(3 * fps),
    SUBTITLE_TIMELINE[0]?.to ?? Math.round(3 * fps)
  );
  if (frame < hookOverlayEndFrames) return null;

  const entry = SUBTITLE_TIMELINE.find((s) => frame >= s.from && frame < s.to);
  if (!entry) return null;

  const relFrame = frame - entry.from;
  const progress = spring({ fps, frame: relFrame, config: { damping: 14, stiffness: 180 } });
  const opacity = interpolate(relFrame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(progress, [0, 1], [0.88, 1]);
  const lines = entry.text.split("\n");
  const lineColors = getLineColors(entry.text, entry.from);
  const isNameCard = /^[123]人目は/.test(entry.text.trim());

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: `${SUBTITLE_STYLE.yPercent}%`,
          left: "50%",
          transform: `translateX(-50%) scale(${scale})`,
          opacity,
          maxWidth: "92%",
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
            const useBox = !isNameCard && line.trim() !== "";
            return (
              <div
                key={`${entry.from}-${index}-${line}`}
                style={{
                  fontFamily: SUBTITLE_STYLE.fontFamily,
                  fontSize: SUBTITLE_STYLE.fontSize,
                  fontWeight: SUBTITLE_STYLE.fontWeight,
                  color: lineColors[index] ?? SUBTITLE_STYLE.color,
                  lineHeight: 0.96,
                  whiteSpace: "pre-wrap",
                  background: useBox ? SUBTITLE_STYLE.background : "transparent",
                  padding: useBox
                    ? `${SUBTITLE_STYLE.paddingV}px ${SUBTITLE_STYLE.paddingH}px`
                    : "0",
                  borderRadius: useBox ? SUBTITLE_STYLE.borderRadius : 0,
                  marginTop: index === 0 ? 0 : 2,
                  WebkitTextStroke: isNameCard
                    ? `4px ${SUBTITLE_STYLE.strokeColor}`
                    : `${SUBTITLE_STYLE.strokeWidth} ${SUBTITLE_STYLE.strokeColor}`,
                  textShadow: SUBTITLE_STYLE.textShadow,
                }}
              >
                {line}
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

const splitHookText = (raw: string): string => {
  const MAX = 4;
  const splitLine = (line: string): string[] => {
    if (line.length <= MAX) return [line];
    const mid = Math.round(line.length / 2);
    return [line.slice(0, mid), line.slice(mid)];
  };
  return raw
    .replace(/\n+/g, "\n")
    .split("\n")
    .flatMap(splitLine)
    .join("\n");
};

export const ViralVideo: React.FC = () => {
  useViralAdultAffiliateFont();
  const { fps } = useVideoConfig();
  const totalFrames = 1887;
  const hookTextStartFrame = SUBTITLE_TIMELINE[0]?.from ?? 0;
  const hookOverlayEndFrames = Math.max(
    Math.round(3 * fps),
    SUBTITLE_TIMELINE[0]?.to ?? Math.round(3 * fps)
  );
  const hookText = splitHookText(SUBTITLE_TIMELINE[0]?.text ?? "");

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* 背景画像 */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <ImageSceneTrack />
      </Sequence>
      {/* フック演出（0〜3秒） */}
      <Sequence from={0} durationInFrames={hookOverlayEndFrames}>
        <Hook
          hookType="statement"
          text={hookText}
          startFrame={hookTextStartFrame}
          endFrame={hookOverlayEndFrames}
          durationFrames={hookOverlayEndFrames}
          fontFamily={VIRAL_ADULT_AFFILIATE_FONT_FAMILY}
          fontSize={240}
          strokeWidth="4px"
          strokeColor={RETRO_STROKE}
          textShadow={RETRO_SHADOW}
          lineColors={HOOK_LINE_COLORS}
        />
      </Sequence>
      {/* パターンインタラプト */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <FlashTrack />
      </Sequence>
      {/* 字幕 */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <SubtitleTrack />
      </Sequence>
      {/* ナレーション（青山龍星 / VOICEVOX） */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <Audio src={staticFile(`viral/${TITLE}/audio/narration.wav`)} volume={1.0} />
      </Sequence>
    </AbsoluteFill>
  );
};
