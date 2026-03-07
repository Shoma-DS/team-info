import React from "react";
import { Composition } from "remotion";
import { ViralVideo } from "./ViralVideo";
import { PLATFORM_CONFIG } from "./types";

/**
 * Root.tsx
 * viral-template-generator スキルが Composition を追記するファイル。
 * Claude はここに生成した Composition を追記する。
 */
export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/*
        === サンプル Composition ===
        Claude が analysis.json から生成した Composition をここに追記する。
        命名規則: Viral-[platform]-[yyyyMMdd]

        例:
        <Composition
          id="Viral-tiktok-20260308"
          component={ViralVideo}
          durationInFrames={Math.ceil(analysis.duration * analysis.fps)}
          fps={analysis.fps}
          width={PLATFORM_CONFIG[analysis.platform].width}
          height={PLATFORM_CONFIG[analysis.platform].height}
          defaultProps={{
            videoSrc: staticFile("input.mp4"),
            analysis: analysisJson,
          }}
        />
      */}
    </>
  );
};
