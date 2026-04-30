import React from "react";
import { AbsoluteFill, Sequence, Audio, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { VIRAL_ADULT_AFFILIATE_FONT_FAMILY } from "../fonts";

export type ViralSection = {
  title: string;
  imageSrc?: string;
  photoSrc?: string;
  fromFrame: number;
  durationFrames: number;
  switchFrame?: number; // default: 90
};

export type ViralSubtitleEntry = {
  from: number;
  to: number;
  text: string;
};

export type ViralTemplateProps = {
  totalFrames: number;
  audioSrc: string;
  subtitles?: ViralSubtitleEntry[];
  hook: {
    text: string;
    imageSrc: string;
    durationFrames: number;
  };
  sections: ViralSection[];
  cta: {
    imageSrc1: string;
    imageSrc2: string;
    switchFrame: number;
    durationFrames: number;
    fromFrame: number;
  };
  backgroundColor?: string;
  isHorizontal?: boolean;
};

const SUBTITLE_STYLE = {
  fontSize: 95,
  fontWeight: "900" as const,
  color: "#000000",
  fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
};

const SubtitleTrack: React.FC<{ subtitles: ViralSubtitleEntry[]; isHorizontal?: boolean }> = ({ subtitles, isHorizontal }) => {
  const frame = useCurrentFrame();

  const entry = subtitles.find((s) => frame >= s.from && frame < s.to);
  if (!entry || !entry.text) return null;

  const currentDuration = entry.to - entry.from;
  const progressInSegment = frame - entry.from;

  const fadeInFrames = 3;
  const fadeOutFrames = 3;
  const opacity = interpolate(
    progressInSegment,
    [0, fadeInFrames, currentDuration - fadeOutFrames, currentDuration],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: "5%",
        opacity,
        pointerEvents: "none",
        zIndex: 100,
      }}
    >
      <div
        style={{
          ...SUBTITLE_STYLE,
          fontSize: isHorizontal ? 55 : 85, // 横動画なら少し小さめ、見切れないようさらに縮小
          textAlign: "center",
          maxWidth: "95%",
          whiteSpace: "pre-wrap",
          lineBreak: "strict",
          wordBreak: "keep-all",
          lineHeight: 1.2,
          textShadow: "0 4px 10px rgba(255,255,255,0.8), 0 0 15px rgba(255,255,255,0.8)", // 読みやすくするための白枠
        }}
      >
        {entry.text}
      </div>
    </AbsoluteFill>
  );
};

const SectionLayout: React.FC<{ section: ViralSection; isHorizontal?: boolean }> = ({ section, isHorizontal }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const switchFrame = section.switchFrame ?? 90;

  const imageScale = spring({
    fps,
    frame: Math.max(0, frame - 5),
    config: { damping: 14, stiffness: 200 }
  });

  const textOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });


  const transitionFrames = 10;
  
  const imageOpacity = interpolate(
    frame,
    [switchFrame, switchFrame + transitionFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const photoOpacity = interpolate(
    frame,
    [switchFrame, switchFrame + transitionFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF", alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: isHorizontal ? "10%" : "4%",
          width: "100%",
          left: 0,
          padding: "0 4%",
          boxSizing: "border-box",
          textAlign: "center",
          opacity: textOpacity,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: isHorizontal ? Math.min(65, 1150 / section.title.length) : Math.min(85, 750 / section.title.length),
            fontWeight: 900,
            fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
            color: "#000000",
            lineHeight: 1.2,
            letterSpacing: "0.01em",
            whiteSpace: "nowrap",
          }}
        >
          {section.title}
        </h2>
      </div>

      <AbsoluteFill style={{ top: isHorizontal ? "25%" : "25%", height: isHorizontal ? "60%" : "40%", display: "flex", justifyContent: "center", alignItems: "center" }}>
        {section.imageSrc && (
          <div
            style={{
              position: "absolute",
              width: "100%",
              height: "100%",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              opacity: imageOpacity,
              transform: `scale(${imageScale * (isHorizontal ? 1.0 : 1.35)})`,
              visibility: frame >= switchFrame + transitionFrames ? "hidden" : "visible"
            }}
          >
            <img
              src={section.imageSrc}
              style={{ 
                maxHeight: "100%", 
                maxWidth: "100%", 
                objectFit: "contain",
              }}
            />
          </div>
        )}

        {section.photoSrc && (
          <div
            style={{
              position: "absolute",
              width: "100%",
              height: "100%",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              opacity: photoOpacity,
              visibility: frame < switchFrame ? "hidden" : "visible"
            }}
          >
            <img
              src={section.photoSrc}
              style={{ 
                width: isHorizontal ? "60%" : "42%",
                height: "auto",
                aspectRatio: "16/9",
                objectFit: "cover",
                borderRadius: "8px",
                border: "3px solid #FFFFFF",
                boxShadow: "0 8px 25px rgba(0,0,0,0.1)"
              }}
            />
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const ViralTemplate: React.FC<ViralTemplateProps> = ({
  totalFrames,
  audioSrc,
  subtitles,
  hook,
  sections,
  cta,
  backgroundColor = "#FAFAFA",
  isHorizontal = false,
}) => {
  return (
    <AbsoluteFill style={{ background: backgroundColor }}>
      <Sequence name="フック" from={0} durationInFrames={hook.durationFrames}>
        <div
          style={{
            position: "absolute",
            bottom: isHorizontal ? "5%" : "8%",
            height: isHorizontal ? "60%" : "45%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          {hook.imageSrc && (
            <img
              src={hook.imageSrc}
              style={{ 
                maxHeight: "100%",
                maxWidth: "90%",
                objectFit: "contain",
                filter: "drop-shadow(0 10px 20px rgba(0,0,0,0.08))"
              }}
            />
          )}
        </div>

        <div style={{ position: "absolute", top: isHorizontal ? "8%" : "8%", width: "100%", display: "flex", justifyContent: "center", zIndex: 10 }}>
            <div
              style={{
                fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
                fontSize: isHorizontal ? 95 : 135,
                fontWeight: 900,
                color: "#ff2a2a",
                textAlign: "center",
                whiteSpace: "pre-wrap",
                lineBreak: "strict",
                wordBreak: "keep-all",
                lineHeight: 1.2,
                textShadow: "0 0 15px white, 0 0 15px white",
              }}
            >
              {hook.text}
            </div>
        </div>
      </Sequence>
      
      {sections.map((section, idx) => (
        <Sequence key={idx} name={`セクション${idx + 1}`} from={section.fromFrame} durationInFrames={section.durationFrames}>
          <SectionLayout section={section} isHorizontal={isHorizontal} />
        </Sequence>
      ))}

      <Sequence name="CTA" from={cta.fromFrame} durationInFrames={cta.durationFrames}>
        <AbsoluteFill style={{ backgroundColor: "white" }}>
          <div style={{ position: "absolute", top: "15%", height: isHorizontal ? "70%" : "55%", width: "100%", display: "flex", justifyContent: "center", alignItems: "center" }}>
            {(() => {
              const frame = useCurrentFrame();
              const src = frame >= cta.switchFrame ? cta.imageSrc2 : cta.imageSrc1;
              if (!src) return null;
              
              const zoomScale = interpolate(frame, [0, cta.durationFrames], [1, 1.05]);

              return (
                <img
                  src={src}
                  style={{
                    maxHeight: "100%",
                    maxWidth: "100%",
                    objectFit: "contain",
                    transform: `scale(${zoomScale})`
                  }}
                />
              );
            })()}
          </div>
        </AbsoluteFill>
      </Sequence>

      {subtitles && subtitles.length > 0 && (
        <Sequence name="字幕" durationInFrames={totalFrames}>
          <SubtitleTrack subtitles={subtitles} isHorizontal={isHorizontal} />
        </Sequence>
      )}

      <Sequence name="音声" durationInFrames={totalFrames}>
        <Audio src={audioSrc} />
      </Sequence>
    </AbsoluteFill>
  );
};
