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
 *  - 背景画像: ImageSceneTrack（1本のSequence） — クロスフェード付き
 *  - 字幕: SubtitleTrack（1本のSequence） — 行ごとに色を設定
 *  - フラッシュ: FlashTrack（1本のSequence）
 *  - フック: 1本のSequence
 *  - 音声: 1本のSequence（<Audio>）
 *
 * 字幕スタイルルール（必須）:
 *  - SUBTITLE_STYLE は viral_patterns.md の「5. 字幕スタイル詳細分析」から導出する
 *  - yPercent: text_regions の avg_y × 100
 *  - fontWeight / color / textShadow: tone + emotional_intensity から選択
 *  - PLATFORM_CONFIG の固定値で上書きしない
 *
 * 名前カードルール（必須）:
 *  - 人物名は「1.人物名」形式で統一（例: "1.釈由美子"）
 *  - isNameCard 判定: /^[1-3]\./.test(text.trim())
 *  - 名前カードの色: #FFE400（鮮黄色）
 *  - 名前カードのフォントサイズ: 通常字幕より大きく（例: 170px）
 *
 * 字幕カードルール（必須）:
 *  - SUBTITLE_TIMELINE は split_subtitles.py --mode card 済みの短いカード字幕を使う
 *  - 表示時の自然な折り返しは Remotion/my-video/src/textLayout.ts の共通ヘルパーに寄せる
 *  - hook は 3〜4 行の短句、本文と CTA は 1〜2 行の短いフレーズカード
 *  - 1行あたり 4〜7 文字前後を目安にし、参照例 gachiNuida20260313Subtitles.ts に寄せる
 *  - テンプレートごとに独自の再分割ロジックを増やさない
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

// ─── タイトル（staticFile パスに使う） ───────────────────────────────────
const TITLE = "[タイトル]"; // 例: "ガチで脱いだ女性芸能人3選_20260313"

// ─── 字幕スタイル（viral_patterns.md の分析結果から Claude が設定する） ──
// adult_affiliate_retro テンプレート（アダルトアフィリ系）の例:
const TEXT_COLOR = "#ffffff";
const STROKE_COLOR = "#000000";
const TEXT_SHADOW = "0 4px 0 rgba(0,0,0,0.85), 0 8px 20px rgba(0,0,0,0.65)";

const SUBTITLE_STYLE = {
  yPercent: 55,             // text_regions avg_y × 100（分析から取得）
  fontSize: 140,            // 字幕の基本フォントサイズ（px）
  fontWeight: "900" as const,
  color: TEXT_COLOR,
  background: undefined,    // 座布団なし（bg_box 系なら "rgba(0,0,0,0.65)" 等）
  paddingH: 0,
  paddingV: 0,
  borderRadius: 0,
  strokeWidth: "2.5px",
  strokeColor: STROKE_COLOR,
  textShadow: TEXT_SHADOW,
  fontFamily: "sans-serif", // フォントをロードする場合は FontFace + useEffect で
};

// ─── フック行色: 黄 → サーモン → ライトピンク → 白 ────────────────────
const HOOK_LINE_COLORS = ["#f4d56f", "#f4a898", "#f0c8d8", "#ffffff"];

// ─── 名前カード色 ─────────────────────────────────────────────────────────
const NAME_COLOR = "#FFE400"; // 鮮黄色（人物カードを目立たせる）
const NAME_COLORS = [NAME_COLOR, NAME_COLOR];

// ─── 行ごとの色を返す関数 ─────────────────────────────────────────────────
const getLineColors = (text: string, from: number): string[] => {
  const lines = text.split("\n");
  const isNameCard = /^[1-3]\./.test(text.trim());
  if (isNameCard) {
    return lines.map((_, i) => NAME_COLORS[i] ?? "#ffffff");
  }
  if (from < 90) {
    // フック期間（0〜3秒）: 黄→サーモン→ライトピンク→白
    return lines.map((_, i) => HOOK_LINE_COLORS[i] ?? HOOK_LINE_COLORS[0]);
  }
  return lines.map(() => SUBTITLE_STYLE.color);
};

// ─── 背景画像タイムライン（subtitles.json と素材一覧から Claude が生成） ─
// motionProfile: "still"=完全静止 / "gentle"=超低速 / "standard"=標準
const FADE_FRAMES = 12; // フェード長（0.4秒 @ 30fps）
const SCENE_TIMELINE: {
  from: number; to: number; src: string;
  motionType?: string; motionIntensity?: number;
  motionProfile?: "standard" | "gentle" | "still";
  originX?: number; originY?: number;
}[] = [
  // hook: 超低速ズームで視線を引き込む
  { from: 0,   to: 90,  src: staticFile(`viral/${TITLE}/materials/00_hook.png`),  motionType: "zoom_in",  motionProfile: "gentle", motionIntensity: 0.5, originX: 0.5, originY: 0.4 },
  // 本編: 静止 / ゆるいパン / 超低速ズームを組み合わせる（落ち着いたテンポ）
  { from: 90,  to: 270, src: staticFile(`viral/${TITLE}/materials/02_s1_1.png`),  motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
  { from: 270, to: 450, src: staticFile(`viral/${TITLE}/materials/02_s1_2.png`),  motionType: "pan_right",motionProfile: "gentle", motionIntensity: 0.4, originX: 0.4, originY: 0.5 },
  // ... 以下 Claude が subtitles.json に合わせて生成
  // CTA: 静止
  { from: 450, to: 600, src: staticFile(`viral/${TITLE}/materials/99_cta.png`),   motionType: "static",   motionProfile: "still",  motionIntensity: 0,   originX: 0.5, originY: 0.5 },
];

// ─── 字幕タイムライン（subtitles.json の segments から生成、または generated/ に分離） ──
// 長い動画では src/viral/generated/[タイトル]Subtitles.ts に分離して import するとよい
// 例: import { SUBTITLE_TIMELINE } from "../generated/[タイトル]Subtitles";
const SUBTITLE_TIMELINE: { from: number; to: number; text: string }[] = [
  { from: 0,  to: 90,  text: "[フック]\n[短句]\n[短句]" },
  { from: 90, to: 140, text: "1.人物名" },
  { from: 140, to: 190, text: "[短い句]\n[続き]" },
  // ... 以下 Claude が生成
];

// ─── パターンインタラプト（セクション境界でフラッシュ） ─────────────────
const INTERRUPT_FRAMES: number[] = [90]; // セクション境界のフレーム番号

// ─── SceneImage: エントリ1件分の画像レンダリング ────────────────────────
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

// ─── ImageSceneTrack: 1本のSequenceで全背景画像を統合（クロスフェード付き）
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

// ─── SubtitleTrack: 行ごとに色を設定できる字幕トラック ────────────────────
// - 冒頭フック期間は return null（Hook が担当するため）
// - 名前カードは isNameCard=true で特大フォント＋黄色
// - 通常字幕は行ごとに getLineColors() で色を割り当てる
// - 表示時の折り返しは共通ヘルパーに任せ、テンプレート側で再分割を増やさない
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
            const useBox = !isNameCard && line.trim() !== "";
            return (
              <div
                key={`${entry.from}-${index}-${line}`}
                style={{
                  fontFamily: SUBTITLE_STYLE.fontFamily,
                  fontSize: isNameCard ? 170 : SUBTITLE_STYLE.fontSize,
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
  const hookTextStartFrame = SUBTITLE_TIMELINE[0]?.from ?? 0;
  const hookOverlayEndFrames = Math.max(
    Math.round(3 * fps),
    SUBTITLE_TIMELINE[0]?.to ?? Math.round(3 * fps)
  );
  const hookText = SUBTITLE_TIMELINE[0]?.text ?? "";

  return (
    <AbsoluteFill style={{ background: "#000" }}>

      {/* ── 背景画像（1本のSequenceで全シーン統合・クロスフェード付き）── */}
      <Sequence name="背景画像" from={0} durationInFrames={totalFrames}>
        <ImageSceneTrack />
      </Sequence>

      {/* ── フック演出（最初の3秒）────────────────────────────────────── */}
      <Sequence name="フック テキスト" from={0} durationInFrames={hookOverlayEndFrames}>
        <Hook
          hookType="statement"
          text={hookText}
          startFrame={hookTextStartFrame}
          endFrame={hookOverlayEndFrames}
          durationFrames={hookOverlayEndFrames}
          fontFamily={SUBTITLE_STYLE.fontFamily}
          fontSize={160}
          strokeWidth={SUBTITLE_STYLE.strokeWidth}
          strokeColor={SUBTITLE_STYLE.strokeColor}
          textShadow={SUBTITLE_STYLE.textShadow}
          lineColors={HOOK_LINE_COLORS}
          paddingTop="65%"
        />
      </Sequence>

      {/* ── パターンインタラプト（1本のSequenceで統合）────────────────── */}
      <Sequence name="フラッシュ 演出" from={0} durationInFrames={totalFrames}>
        <FlashTrack />
      </Sequence>

      {/* ── 字幕（1本のSequenceで統合・行ごと色設定）────────────────── */}
      <Sequence name="字幕" from={0} durationInFrames={totalFrames}>
        <SubtitleTrack />
      </Sequence>

      {/* ── ナレーション（VOICEVOX）──────────────────────────────────── */}
      <Sequence name="音声 ナレーション" from={0} durationInFrames={totalFrames}>
        <Audio src={staticFile(`viral/${TITLE}/audio/narration.wav`)} volume={1.0} />
      </Sequence>

    </AbsoluteFill>
  );
};
