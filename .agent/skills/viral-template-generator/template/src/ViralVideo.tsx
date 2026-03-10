/**
 * ViralVideo.tsx
 *
 * このファイルは viral-template-generator スキルが
 * subtitles.json と materials/ から自動生成するメインコンポーネント。
 *
 * Claude が生成する際はこのファイルを実際のコンテンツで置き換える。
 * 以下は Phase F の生成規則に従ったサンプル実装。
 *
 * 構造ルール（必須）:
 *  - 同種・非重複素材は <Sequence> 1本に統合し、現在フレームでアクティブ素材を選ぶ
 *  - 背景画像: ImageSceneTrack（1本のSequence）
 *  - 字幕: SubtitleTrack（1本のSequence）
 *  - フラッシュ: FlashTrack（1本のSequence）
 *  - フック: 1本のSequence
 *
 * 字幕スタイルルール（必須）:
 *  - SUBTITLE_STYLE は viral_patterns.md の「5. 字幕スタイル詳細分析」から導出する
 *  - yPercent: text_regions の avg_y × 100
 *  - fontWeight / color / bgColor / textShadow: tone + emotional_intensity から選択
 *  - PLATFORM_CONFIG の固定値で上書きしない
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PLATFORM_CONFIG } from "./types";
import { ImageScene } from "./components/ImageScene";
import { Hook } from "./components/Hook";

// ─── プラットフォーム設定 ────────────────────────────────────────────────
const PLATFORM = "shorts" as const;
const _CONFIG = PLATFORM_CONFIG[PLATFORM]; // フォールバック用（SUBTITLE_STYLE で上書き）

// ─── 字幕スタイル（viral_patterns.md の分析結果から Claude が設定する） ──
// tone=entertainment, emotional_intensity=high の場合の例:
const SUBTITLE_STYLE = {
  yPercent: 75,                                               // text_regions avg_y × 100
  fontSize: 52,                                               // PLATFORM基準 × tone倍率
  fontWeight: "900" as const,                                 // entertainment+high → 極太
  color: "#ffffff",                                           // 基本白
  bgColor: "rgba(0,0,0,0.65)",                               // entertainment → 濃いめ
  textShadow: "0 2px 12px rgba(0,0,0,0.8), 0 0 4px #000",  // 二重シャドウ
  letterSpacing: "0.02em",
  strokeWidth: "2px",                                         // テキスト輪郭
  strokeColor: "#000000",
};

// ─── 背景画像タイムライン（subtitles.json と素材一覧から Claude が生成） ─
const SCENE_TIMELINE: { from: number; to: number; src: string }[] = [
  { from: 0,   to: 90,  src: staticFile("materials/00_hook.jpg") },
  { from: 90,  to: 180, src: staticFile("materials/01_opening.jpg") },
  // ... 以下 Claude が生成
];

// ─── 字幕タイムライン（subtitles.json の segments から Claude が生成） ──
const SUBTITLE_TIMELINE: { from: number; to: number; text: string }[] = [
  { from: 0,  to: 90,  text: "[フック文章]" },
  { from: 90, to: 180, text: "[予告文章]" },
  // ... 以下 Claude が生成
];

// ─── パターンインタラプト（viral_patterns.md の平均タイミング × fps） ───
const INTERRUPT_FRAMES: number[] = [];

// ─── ImageSceneTrack: 1本のSequenceで全背景画像を統合 ────────────────────
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

// ─── SubtitleTrack: 1本のSequenceで全字幕を統合 ──────────────────────────
// SUBTITLE_STYLE を使って参照動画に忠実なスタイルを再現する
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
            lineHeight: 1.35,
            padding: "0.18em 0.6em",
            borderRadius: 10,
            background: SUBTITLE_STYLE.bgColor,
            textShadow: SUBTITLE_STYLE.textShadow,
            // テキスト輪郭（WebKit）
            WebkitTextStroke: `${SUBTITLE_STYLE.strokeWidth} ${SUBTITLE_STYLE.strokeColor}`,
          }}
        >
          {entry.text}
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ─── FlashTrack: 1本のSequenceで全パターンインタラプトを統合 ─────────────
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

// ─── メインコンポーネント ─────────────────────────────────────────────────
export const ViralVideo: React.FC = () => {
  const { fps } = useVideoConfig();
  const totalFrames = Math.ceil(58.0 * fps); // subtitles.json の total_frames を使う
  const hookDuration = Math.round(3 * fps);

  return (
    <AbsoluteFill style={{ background: "#000" }}>

      {/* ── 背景画像（1本のSequenceで全シーン統合） ────────────── */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <ImageSceneTrack />
      </Sequence>

      {/* ── フック演出（最初の3秒） ────────────────────────────── */}
      <Sequence from={0} durationInFrames={hookDuration}>
        <Hook
          hookType="statement"
          text={SUBTITLE_TIMELINE[0]?.text ?? ""}
          durationFrames={hookDuration}
        />
      </Sequence>

      {/* ── パターンインタラプト（1本のSequenceで統合） ────────── */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <FlashTrack />
      </Sequence>

      {/* ── 字幕（1本のSequenceで統合・SUBTITLE_STYLEを適用） ─── */}
      <Sequence from={0} durationInFrames={totalFrames}>
        <SubtitleTrack />
      </Sequence>

    </AbsoluteFill>
  );
};
