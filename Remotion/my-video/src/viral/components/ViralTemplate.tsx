import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { formatWrappedText } from "../../textLayout";
import { VIRAL_ADULT_AFFILIATE_FONT_FAMILY } from "../fonts";

export type ViralSection = {
  title: string;
  imageSrc?: string;
  photoSrc?: string;
  fromFrame: number;
  durationFrames: number;
  switchFrame?: number;
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
  fontWeight: "900" as const,
  color: "#000000",
  fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
};

const getLongestLineLength = (text: string) => {
  return Math.max(...text.split("\n").map((line) => line.length), 1);
};

const SubtitleTrack: React.FC<{
  subtitles: ViralSubtitleEntry[];
  isHorizontal?: boolean;
}> = ({ subtitles, isHorizontal }) => {
  const frame = useCurrentFrame();
  const entry = subtitles.find((s) => frame >= s.from && frame < s.to);

  if (!entry || !entry.text) {
    return null;
  }

  const currentDuration = entry.to - entry.from;
  const progressInSegment = frame - entry.from;
  const opacity = interpolate(
    progressInSegment,
    [0, 3, currentDuration - 3, currentDuration],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const displayText = formatWrappedText(entry.text, {
    maxCharsPerLine: isHorizontal ? 23 : 12,
    preserveExistingLineBreaks: false,
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: isHorizontal ? "5%" : "16%",
        opacity,
        pointerEvents: "none",
        zIndex: 100,
      }}
    >
      <div
        style={{
          ...SUBTITLE_STYLE,
          fontSize: isHorizontal ? 55 : 76,
          textAlign: "center",
          maxWidth: isHorizontal ? "95%" : "88%",
          whiteSpace: "pre-wrap",
          lineBreak: "strict",
          wordBreak: "keep-all",
          lineHeight: isHorizontal ? 1.2 : 1.18,
          letterSpacing: 0,
          textShadow:
            "0 4px 10px rgba(255,255,255,0.86), 0 0 15px rgba(255,255,255,0.86)",
        }}
      >
        {displayText}
      </div>
    </AbsoluteFill>
  );
};

const SectionLayout: React.FC<{
  section: ViralSection;
  isHorizontal?: boolean;
}> = ({ section, isHorizontal }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const switchFrame = section.switchFrame ?? 90;
  const titleText = formatWrappedText(section.title, {
    maxCharsPerLine: isHorizontal ? 18 : 10,
    preserveExistingLineBreaks: false,
  });

  const imageScale = spring({
    fps,
    frame: Math.max(0, frame - 5),
    config: { damping: 14, stiffness: 200 },
  });
  const textOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const imageOpacity = interpolate(frame, [switchFrame, switchFrame + 10], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const photoOpacity = interpolate(frame, [switchFrame, switchFrame + 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF", alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: isHorizontal ? "10%" : "4%",
          width: "100%",
          left: 0,
          padding: isHorizontal ? "0 4%" : "0 6%",
          boxSizing: "border-box",
          textAlign: "center",
          opacity: textOpacity,
          zIndex: 2,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: isHorizontal
              ? Math.min(65, 1150 / section.title.length)
              : Math.min(74, 560 / getLongestLineLength(titleText)),
            fontWeight: 900,
            fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
            color: "#000000",
            lineHeight: isHorizontal ? 1.2 : 1.12,
            letterSpacing: 0,
            whiteSpace: "pre-wrap",
          }}
        >
          {titleText}
        </h2>
      </div>

      <AbsoluteFill
        style={{
          top: isHorizontal ? "25%" : "15%",
          height: isHorizontal ? "60%" : "50%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
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
              transform: `scale(${imageScale * (isHorizontal ? 1 : 1.18)})`,
              visibility: frame >= switchFrame + 10 ? "hidden" : "visible",
            }}
          >
            <img
              src={section.imageSrc}
              style={{
                maxHeight: "100%",
                maxWidth: isHorizontal ? "100%" : "94%",
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
              visibility: frame < switchFrame ? "hidden" : "visible",
            }}
          >
            <img
              src={section.photoSrc}
              style={{
                width: isHorizontal ? "60%" : "88%",
                height: "auto",
                aspectRatio: "16/9",
                objectFit: "cover",
                borderRadius: "8px",
                border: "3px solid #FFFFFF",
                boxShadow: "0 10px 28px rgba(0,0,0,0.12)",
              }}
            />
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const CtaLayout: React.FC<{
  cta: ViralTemplateProps["cta"];
  isHorizontal?: boolean;
}> = ({ cta, isHorizontal }) => {
  const frame = useCurrentFrame();
  const src = frame >= cta.switchFrame ? cta.imageSrc2 : cta.imageSrc1;
  const zoomScale = interpolate(frame, [0, cta.durationFrames], [1, 1.05]);

  if (!src) {
    return null;
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "white" }}>
      <div
        style={{
          position: "absolute",
          top: isHorizontal ? "15%" : "12%",
          height: isHorizontal ? "70%" : "62%",
          width: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <img
          src={src}
          style={{
            maxHeight: "100%",
            maxWidth: isHorizontal ? "100%" : "92%",
            objectFit: "contain",
            transform: `scale(${zoomScale})`,
          }}
        />
      </div>
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
  const hookText = formatWrappedText(hook.text, {
    maxCharsPerLine: isHorizontal ? 18 : 9,
    preserveExistingLineBreaks: true,
  });

  return (
    <AbsoluteFill style={{ background: backgroundColor }}>
      <Sequence name="Hook" from={0} durationInFrames={hook.durationFrames}>
        <div
          style={{
            position: "absolute",
            bottom: isHorizontal ? "5%" : "6%",
            height: isHorizontal ? "60%" : "53%",
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
                maxWidth: isHorizontal ? "90%" : "92%",
                objectFit: "contain",
                filter: "drop-shadow(0 10px 20px rgba(0,0,0,0.08))",
              }}
            />
          )}
        </div>

        <div
          style={{
            position: "absolute",
            top: isHorizontal ? "8%" : "7%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            zIndex: 10,
            padding: isHorizontal ? "0 4%" : "0 6%",
            boxSizing: "border-box",
          }}
        >
          <div
            style={{
              fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
              fontSize: isHorizontal ? 95 : Math.min(122, 540 / getLongestLineLength(hookText)),
              fontWeight: 900,
              color: "#ff2a2a",
              textAlign: "center",
              whiteSpace: "pre-wrap",
              lineBreak: "strict",
              wordBreak: "keep-all",
              lineHeight: isHorizontal ? 1.2 : 1.08,
              letterSpacing: 0,
              textShadow: "0 0 15px white, 0 0 15px white",
            }}
          >
            {hookText}
          </div>
        </div>
      </Sequence>

      {sections.map((section, idx) => (
        <Sequence
          key={idx}
          name={`Section${idx + 1}`}
          from={section.fromFrame}
          durationInFrames={section.durationFrames}
        >
          <SectionLayout section={section} isHorizontal={isHorizontal} />
        </Sequence>
      ))}

      <Sequence name="CTA" from={cta.fromFrame} durationInFrames={cta.durationFrames}>
        <CtaLayout cta={cta} isHorizontal={isHorizontal} />
      </Sequence>

      {subtitles && subtitles.length > 0 && (
        <Sequence name="Subtitles" durationInFrames={totalFrames}>
          <SubtitleTrack subtitles={subtitles} isHorizontal={isHorizontal} />
        </Sequence>
      )}

      <Sequence name="Audio" durationInFrames={totalFrames}>
        <Audio src={audioSrc} />
      </Sequence>
    </AbsoluteFill>
  );
};
