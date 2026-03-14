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
const TEXT_COLOR = "#ffffff";
const STROKE_COLOR = "#000000";
const TEXT_SHADOW = "0 4px 0 rgba(0,0,0,0.85), 0 8px 20px rgba(0,0,0,0.65)";

// 字幕スタイル（参考画像: 大谷翔平とヤリたがってた女性芸能人3選 に合わせて更新）
// 白文字 / 黒枠 / 半透明黒影 / 背景ボックスなし / Y=52%
const SUBTITLE_STYLE = {
  yPercent: 55,
  fontSize: 140,
  fontWeight: "900" as const,
  color: TEXT_COLOR,
  background: undefined,
  paddingH: 0,
  paddingV: 0,
  borderRadius: 0,
  strokeWidth: "2.5px",
  strokeColor: STROKE_COLOR,
  textShadow: TEXT_SHADOW,
  fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
};

// フック行色: 黄 → サーモン → ライトピンク → 白（参考動画5本から抽出）
const HOOK_LINE_COLORS = ["#f4d56f", "#f4a898", "#f0c8d8", "#ffffff"];
const NAME_COLORS = [TEXT_COLOR, TEXT_COLOR];

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
    { from: 0, to: 90, src: staticFile(`viral/${TITLE}/materials/00_hook.jpg`), motionType: "zoom_in", motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
    { from: 90, to: 258, src: staticFile(`viral/${TITLE}/materials/02_s1_1.jpg`), motionType: "shake", motionIntensity: 1.5, originX: 0.5, originY: 0.5 },
    { from: 258, to: 462, src: staticFile(`viral/${TITLE}/materials/02_s1_2.jpg`), motionType: "zoom_in", motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
    { from: 462, to: 586, src: staticFile(`viral/${TITLE}/materials/02_s1_3.jpg`), motionType: "pan_right", motionIntensity: 1.2, originX: 0.3, originY: 0.5 },
    { from: 586, to: 733, src: staticFile(`viral/${TITLE}/materials/03_s2_1.jpg`), motionType: "shake", motionIntensity: 1.5, originX: 0.5, originY: 0.5 },
    { from: 733, to: 1036, src: staticFile(`viral/${TITLE}/materials/03_s2_2.jpg`), motionType: "zoom_in", motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
    { from: 1036, to: 1153, src: staticFile(`viral/${TITLE}/materials/03_s2_3.jpg`), motionType: "pan_left", motionIntensity: 1.2, originX: 0.7, originY: 0.5 },
    { from: 1153, to: 1333, src: staticFile(`viral/${TITLE}/materials/04_s3_1.jpg`), motionType: "shake", motionIntensity: 1.5, originX: 0.5, originY: 0.5 },
    { from: 1333, to: 1481, src: staticFile(`viral/${TITLE}/materials/04_s3_2.jpg`), motionType: "zoom_out", motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
    { from: 1481, to: 1617, src: staticFile(`viral/${TITLE}/materials/04_s3_3.jpg`), motionType: "pan_right", motionIntensity: 1.2, originX: 0.3, originY: 0.5 },
    { from: 1617, to: 1887, src: staticFile(`viral/${TITLE}/materials/99_cta.jpg`), motionType: "zoom_in", motionIntensity: 0.5, originX: 0.5, originY: 0.5 },
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
                  WebkitTextStroke: `${SUBTITLE_STYLE.strokeWidth} ${SUBTITLE_STYLE.strokeColor}`,
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
  const hookText = SUBTITLE_TIMELINE[0]?.text ?? ""; // 手動改行を使うため自動分割をバイパス

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
          fontSize={160}
          strokeWidth="3px"
          strokeColor={STROKE_COLOR}
          textShadow={TEXT_SHADOW}
          lineColors={HOOK_LINE_COLORS}
          paddingTop="65%"
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
