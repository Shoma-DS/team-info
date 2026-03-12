/**
 * ViralVideo.tsx — スタイル反則レベルのアイドル3選
 * 生成日: 2026-03-12 | プラットフォーム: shorts | 尺: 55秒 / 1650フレーム
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
import { ImageScene } from "./components/ImageScene";
import { Hook } from "./components/Hook";
import { SUBTITLE_TIMELINE } from "./generated/スタイル反則アイドル3選Subtitles";

const TITLE = "スタイル反則アイドル3選_20260312";

// 字幕スタイル
// 分析結果: 7本中4本が「座布団（暗い背景ボックス）」スタイル
//   text_color: 淡いピンクベージュ系 (#ebc1b9〜#c2aaa8) ← 実測値
//   background_box: rgba(19〜27, 10〜20, 11〜18, 0.83〜0.94) ← 4本平均
//   stroke: なし（座布団ありのため不要）
//   font_size_px: 0（解析不可）→ Shorts platform default 48px
//   text_regions Y座標: 0.60〜0.90 → yPercent: 70
//   font: 角ゴシック（Hiragino Sans）に寄せてフックと統一
const SUBTITLE_STYLE = {
  yPercent: 70,
  fontSize: 48,
  fontWeight: "900" as const,
  color: "#ebc1b9",
  background: "rgba(22,14,14,0.88)",
  paddingH: 22,
  paddingV: 10,
  borderRadius: 6,
  letterSpacing: "0.02em",
  fontFamily:
    '"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", sans-serif',
};

// 名前カード・フックは強調色（座布団なし・ゴールド）
const NAME_COLORS = ["#f4d56f", "#ffffff"];

const getLineColors = (text: string, from: number): string[] => {
  const lines = text.split("\n");
  if (/^[123]\.\s/.test(text.trim())) {
    return lines.map((_, i) => NAME_COLORS[i] ?? "#ffffff");
  }
  if (from < 190) {
    return lines.map((_, i) => (i === 0 ? "#f4d56f" : "#ffffff"));
  }
  return lines.map(() => SUBTITLE_STYLE.color);
};

// 背景画像タイムライン（字幕切り替えに合わせてシーン変化）
const SCENE_TIMELINE: { from: number; to: number; src: string; motionType?: string; motionIntensity?: number }[] = [
  { from: 0,    to: 94,   src: staticFile(`viral/${TITLE}/materials/00_hook.jpg`),    motionType: "zoom_in",  motionIntensity: 1.0 },
  { from: 94,   to: 188,  src: staticFile(`viral/${TITLE}/materials/01_opening.png`), motionType: "zoom_in",  motionIntensity: 0.8 },
  { from: 188,  to: 305,  src: staticFile(`viral/${TITLE}/materials/02_s1_1.jpg`),   motionType: "zoom_in",  motionIntensity: 1.0 },
  { from: 305,  to: 382,  src: staticFile(`viral/${TITLE}/materials/02_s1_2.jpg`),   motionType: "pan_right", motionIntensity: 1.0 },
  { from: 382,  to: 581,  src: staticFile(`viral/${TITLE}/materials/02_s1_3.jpg`),   motionType: "zoom_out", motionIntensity: 0.8 },
  { from: 581,  to: 694,  src: staticFile(`viral/${TITLE}/materials/03_s2_1.jpg`),   motionType: "zoom_in",  motionIntensity: 1.0 },
  { from: 694,  to: 786,  src: staticFile(`viral/${TITLE}/materials/03_s2_2.jpg`),   motionType: "pan_left", motionIntensity: 1.0 },
  { from: 786,  to: 963, src: staticFile(`viral/${TITLE}/materials/03_s2_3.jpg`),   motionType: "zoom_in",  motionIntensity: 0.8 },
  { from: 963, to: 1130, src: staticFile(`viral/${TITLE}/materials/04_s3_1.jpg`),   motionType: "zoom_in",  motionIntensity: 1.2 },
  { from: 1130, to: 1235, src: staticFile(`viral/${TITLE}/materials/04_s3_2.jpg`),   motionType: "pan_right", motionIntensity: 1.0 },
  { from: 1235, to: 1441, src: staticFile(`viral/${TITLE}/materials/04_s3_3.jpg`),   motionType: "zoom_out", motionIntensity: 0.8 },
  { from: 1441, to: 1486, src: staticFile(`viral/${TITLE}/materials/99_cta.png`),    motionType: "zoom_in",  motionIntensity: 0.5 },
];

// パターンインタラプト (3s=90f, 21.4s=643f, 35.8s=1074f)
const INTERRUPT_FRAMES: number[] = [90, 581, 963];

const ImageSceneTrack: React.FC = () => {
  const frame = useCurrentFrame();
  const entry =
    SCENE_TIMELINE.find((s) => frame >= s.from && frame < s.to) ??
    SCENE_TIMELINE[SCENE_TIMELINE.length - 1];
  return (
    <AbsoluteFill>
      <ImageScene
        src={entry.src}
        motionType={(entry.motionType as "zoom_in" | "zoom_out" | "pan_right" | "pan_left" | "static") ?? "zoom_in"}
        motionIntensity={entry.motionIntensity ?? 1.0}
      />
    </AbsoluteFill>
  );
};

const SubtitleTrack: React.FC = () => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const hookOverlayEndFrames = Math.max(Math.round(3 * fps), SUBTITLE_TIMELINE[0]?.to ?? Math.round(3 * fps));
  if (frame < hookOverlayEndFrames) return null;

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
          {lines.map((line, index) => {
            const isNameCard = /^[123]\.\s/.test(entry.text.trim());
            const isHook = entry.from < 190;
            const useBox = !isNameCard && !isHook && line.trim() !== "";
            return (
              <div
                key={`${entry.from}-${index}-${line}`}
                style={{
                  fontFamily: SUBTITLE_STYLE.fontFamily,
                  fontSize: SUBTITLE_STYLE.fontSize,
                  fontWeight: SUBTITLE_STYLE.fontWeight,
                  color: lineColors[index] ?? SUBTITLE_STYLE.color,
                  letterSpacing: SUBTITLE_STYLE.letterSpacing,
                  lineHeight: 1.3,
                  whiteSpace: "nowrap",
                  background: useBox ? SUBTITLE_STYLE.background : "transparent",
                  padding: useBox
                    ? `${SUBTITLE_STYLE.paddingV}px ${SUBTITLE_STYLE.paddingH}px`
                    : "0",
                  borderRadius: useBox ? SUBTITLE_STYLE.borderRadius : 0,
                  marginTop: index === 0 ? 0 : 4,
                  WebkitTextStroke: isNameCard || isHook ? "3px #1d1b1a" : "none",
                  textShadow: isNameCard || isHook
                    ? "0 4px 0 rgba(0,0,0,0.4)"
                    : "none",
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

// Hook テキストを Hook コンポーネントの最大幅（82% × 1080px = 885px）に収まるよう
// 日本語文節境界を考慮して1行あたり最大11文字で分割する
const splitHookText = (raw: string): string => {
  const MAX = 11;
  // 文節区切りとして使える文字（ひらがなの活用語尾・助詞・助動詞の後など）
  const SPLIT_AFTER = "いうえおたてしなにでがをはもとかのくきよわぞぜねちつぬればれるれ";

  const splitLine = (line: string): string[] => {
    if (line.length <= MAX) return [line];
    const mid = Math.round(line.length / 2);
    const range = Math.floor(MAX * 0.4);

    // mid付近で、直前がひらがな活用語尾・助詞の位置を探す
    let bestIdx = mid;
    let bestScore = Infinity;
    for (let i = Math.max(1, mid - range); i <= Math.min(line.length - 1, mid + range); i++) {
      const prev = line[i - 1];
      const score = Math.abs(i - mid);
      if (SPLIT_AFTER.includes(prev) && score < bestScore) {
        bestScore = score;
        bestIdx = i;
      }
    }
    const first = line.slice(0, bestIdx);
    const rest = line.slice(bestIdx);
    return rest.length > MAX ? [first, ...splitLine(rest)] : [first, rest];
  };

  return raw
    .replace(/\n+/g, "\n")
    .split("\n")
    .flatMap(splitLine)
    .join("\n");
};

export const ViralVideo: React.FC = () => {
  const { fps } = useVideoConfig();
  const totalFrames = 1545;
  const hookTextStartFrame = SUBTITLE_TIMELINE[0]?.from ?? 0;
  const hookOverlayEndFrames = Math.max(Math.round(3 * fps), SUBTITLE_TIMELINE[0]?.to ?? Math.round(3 * fps));
  const hookText = splitHookText(SUBTITLE_TIMELINE[0]?.text ?? "");

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence from={0} durationInFrames={totalFrames}>
        <ImageSceneTrack />
      </Sequence>
      <Sequence from={0} durationInFrames={hookOverlayEndFrames}>
        <Hook
          hookType="statement"
          text={hookText}
          startFrame={hookTextStartFrame}
          endFrame={hookOverlayEndFrames}
          durationFrames={hookOverlayEndFrames}
        />
      </Sequence>
      <Sequence from={0} durationInFrames={totalFrames}>
        <FlashTrack />
      </Sequence>
      <Sequence from={0} durationInFrames={totalFrames}>
        <SubtitleTrack />
      </Sequence>
      {/* ナレーション音源（青山龍星 / VOICEVOX） */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <Audio src={staticFile(`viral/${TITLE}/audio/narration_jetcut.wav`)} volume={1.0} />
      </Sequence>
    </AbsoluteFill>
  );
};
