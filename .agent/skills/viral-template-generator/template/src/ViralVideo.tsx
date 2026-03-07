/**
 * ViralVideo.tsx
 *
 * このファイルは viral-template-generator スキルが
 * analysis.json から自動生成するメインコンポーネントです。
 *
 * Claude が生成する際は、このファイルを analysis.json の内容で置き換えます。
 * 以下はスキルが生成するコードの参照実装（サンプル）です。
 */
import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useVideoConfig,
} from "remotion";
import { AnalysisJson, PLATFORM_CONFIG } from "./types";
import { Scene } from "./components/Scene";
import { Subtitle } from "./components/Subtitle";
import { ZoomEffect } from "./components/ZoomEffect";
import { Hook } from "./components/Hook";

// ─── ここは Claude が analysis.json を読んで書き換える ─────────────────────
// analysis.json のパスをビルド時にインポートするか、
// props として渡す形にする。
// 生成時は以下のように analysis をハードコードする:
//
// const analysis: AnalysisJson = { ...json contents... };

interface ViralVideoProps {
  videoSrc: string;        // 元動画のパス (staticFile() で指定)
  analysis: AnalysisJson;  // analysis.json の内容
}

export const ViralVideo: React.FC<ViralVideoProps> = ({ videoSrc, analysis }) => {
  const { fps } = useVideoConfig();
  const { platform, video_structure, speech_structure, viral_structure } = analysis;
  const config = PLATFORM_CONFIG[platform];

  const { cuts, camera_motion } = video_structure;
  const { transcript } = speech_structure;
  const { hook_time, hook_type, pattern_interrupts } = viral_structure;

  // フックテキスト（最初の発話）
  const hookText = transcript[0]?.text ?? "";

  // ズームが必要なシーン（camera_motion に zoom があるカット）
  const zoomTimes = new Set(
    camera_motion.filter((m) => m.type === "zoom").map((m) => Math.floor(m.start))
  );

  return (
    <AbsoluteFill style={{ background: "#000" }}>

      {/* ── シーン群 ─────────────────────────────────────── */}
      {cuts.map((cut, i) => {
        const from = Math.round(cut.start * fps);
        const dur = Math.max(1, Math.round((cut.end - cut.start) * fps));
        const needsZoom = zoomTimes.has(Math.floor(cut.start));

        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            {needsZoom ? (
              <ZoomEffect startScale={1.0} endScale={1.12} durationFrames={dur}>
                <Scene videoSrc={videoSrc} cut={cut} />
              </ZoomEffect>
            ) : (
              <Scene videoSrc={videoSrc} cut={cut} />
            )}
          </Sequence>
        );
      })}

      {/* ── フック演出 (最初の3秒) ────────────────────────── */}
      {hook_type !== "unknown" && (
        <Sequence from={Math.round(hook_time * fps)} durationInFrames={Math.round(3 * fps)}>
          <Hook
            hookType={hook_type}
            text={hookText}
            durationFrames={Math.round(3 * fps)}
          />
        </Sequence>
      )}

      {/* ── パターンインタラプト (フラッシュ) ─────────────── */}
      {pattern_interrupts.map((t, i) => (
        <Sequence key={`pi-${i}`} from={Math.round(t * fps)} durationInFrames={6}>
          <AbsoluteFill
            style={{ background: "white", opacity: 0.25, pointerEvents: "none" }}
          />
        </Sequence>
      ))}

      {/* ── 字幕 ─────────────────────────────────────────── */}
      {transcript.map((seg, i) => {
        const from = Math.round(seg.start * fps);
        const dur = Math.max(1, Math.round((seg.end - seg.start) * fps));
        return (
          <Sequence key={`sub-${i}`} from={from} durationInFrames={dur}>
            <Subtitle
              text={seg.text}
              fontSize={config.subtitleFontSize}
              yPercent={config.subtitleY}
              platform={platform}
            />
          </Sequence>
        );
      })}

    </AbsoluteFill>
  );
};
