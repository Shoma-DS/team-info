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
// 二重枠: テキストを2レイヤー重ねて WebkitTextStroke で白外枠・黒内枠を描く（角が滑らか）
// 外枠層: WebkitTextStroke "20px #fff" → 約10px が外側に張り出す白リング
// 内枠層: WebkitTextStroke "6px #000" → 約3px の黒リングで白と文字の境界を締める
const OUTER_STROKE = "20px";
const OUTER_STROKE_COLOR = "#ffffff";
const DROP_SHADOW = "0 4px 0 rgba(0,0,0,0.85), 0 8px 20px rgba(0,0,0,0.65)";

// 字幕スタイル: 白文字 / 黒内枠 / 白外枠（2レイヤー重ね）/ 背景ボックスなし
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

// フック行色: 黄 → サーモン → ライトピンク → 白（参考動画5本から抽出）
const HOOK_LINE_COLORS = ["#f4d56f", "#f4a898", "#f0c8d8", "#ffffff"];
const NAME_COLOR = "#FFE400"; // 参考画像スタイル: 鮮黄色
const NAME_COLORS = [NAME_COLOR, NAME_COLOR];

const getLineColors = (text: string, from: number): string[] => {
  const lines = text.split("\n");
  const isNameCard = /^[1-3]\./.test(text.trim());
  if (isNameCard) {
    return lines.map((_, i) => NAME_COLORS[i] ?? "#ffffff");
  }
  if (from < 90) {
    return lines.map((_, i) => HOOK_LINE_COLORS[i] ?? HOOK_LINE_COLORS[0]);
  }
  return lines.map(() => SUBTITLE_STYLE.color);
};

// 背景画像タイムライン（落ち着いたテンポ: 基本静止 / 要所だけ超低速ズーム or ゆるいパン）
const FADE_FRAMES = 12; // フェード長: 0.4秒
const SCENE_TIMELINE: {
  from: number; to: number; src: string;
  motionType?: string; motionIntensity?: number;
  motionProfile?: "standard" | "gentle" | "still";
  originX?: number; originY?: number;
}[] = [
    // hook: 超低速ズームで視線を引き込む
    { from: 0,    to: 90,   src: staticFile(`viral/${TITLE}/materials/00_hook.png`),  motionType: "zoom_in",  motionProfile: "gentle", motionIntensity: 0.5, originX: 0.5, originY: 0.4 },
    // s1: 静止 → ゆるいパン → 静止
    { from: 90,   to: 258,  src: staticFile(`viral/${TITLE}/materials/02_s1_1.png`),  motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
    { from: 258,  to: 462,  src: staticFile(`viral/${TITLE}/materials/02_s1_2.png`),  motionType: "pan_right",motionProfile: "gentle", motionIntensity: 0.4, originX: 0.4, originY: 0.5 },
    { from: 462,  to: 586,  src: staticFile(`viral/${TITLE}/materials/02_s1_3.png`),  motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
    // s2: 超低速ズーム → 静止 → ゆるいパン
    { from: 586,  to: 733,  src: staticFile(`viral/${TITLE}/materials/03_s2_1.png`),  motionType: "zoom_in",  motionProfile: "gentle", motionIntensity: 0.4, originX: 0.5, originY: 0.4 },
    { from: 733,  to: 1036, src: staticFile(`viral/${TITLE}/materials/03_s2_2.png`),  motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
    { from: 1036, to: 1153, src: staticFile(`viral/${TITLE}/materials/03_s2_3.png`),  motionType: "pan_left", motionProfile: "gentle", motionIntensity: 0.4, originX: 0.6, originY: 0.5 },
    // s3: 静止 → 超低速ズームアウト → ゆるいパン
    { from: 1153, to: 1333, src: staticFile(`viral/${TITLE}/materials/04_s3_1.png`),  motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
    { from: 1333, to: 1481, src: staticFile(`viral/${TITLE}/materials/04_s3_2.png`),  motionType: "zoom_out", motionProfile: "gentle", motionIntensity: 0.4, originX: 0.5, originY: 0.4 },
    { from: 1481, to: 1617, src: staticFile(`viral/${TITLE}/materials/04_s3_3.png`),  motionType: "pan_right",motionProfile: "gentle", motionIntensity: 0.4, originX: 0.4, originY: 0.5 },
    // CTA: 静止
    { from: 1617, to: 1887, src: staticFile(`viral/${TITLE}/materials/99_cta.png`),   motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
  ];

// パターンインタラプト（エピソード切り替え: 3s=90f / 19.5s=586f / 38.4s=1153f）
const INTERRUPT_FRAMES: number[] = [90, 586, 1153];

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
                {/* 外枠レイヤー: 白い太いストローク + ドロップシャドウ */}
                <div style={{
                  ...sharedStyle,
                  color: OUTER_STROKE_COLOR,
                  WebkitTextStroke: `${outerStroke} ${OUTER_STROKE_COLOR}`,
                  textShadow: DROP_SHADOW,
                }}>
                  {line}
                </div>
                {/* 内枠レイヤー: 黒ストローク + 文字色（絶対配置で重ねる） */}
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
          strokeWidth="1.5px"
          strokeColor={STROKE_COLOR}
          textShadow={DROP_SHADOW}
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
