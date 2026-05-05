import React from "react";
import {
  AbsoluteFill,
  Audio,
  continueRender,
  delayRender,
  Img,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { formatWrappedText } from "../../textLayout";
import { VIRAL_ADULT_AFFILIATE_FONT_FAMILY } from "../fonts";

export type ViralVisual = {
  src: string;
  kind: "illustration" | "photo";
  fromFrame: number;
  toFrame?: number;
};

export type ViralSection = {
  title: string;
  imageSrc?: string;
  photoSrc?: string;
  visuals?: ViralVisual[];
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
    callouts?: {
      text: string;
      fromFrame: number;
      imageSrc?: string;
    }[];
  };
  sections: ViralSection[];
  cta: {
    imageSrc1: string;
    imageSrc2: string;
    switchFrame: number;
    durationFrames: number;
    fromFrame: number;
  };
  sfx?: {
    src: string;
    fromFrame: number;
    volume?: number;
    durationFrames?: number;
  }[];
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

const getActiveVisual = (section: ViralSection, frame: number): ViralVisual | null => {
  if (section.visuals && section.visuals.length > 0) {
    return (
      section.visuals.find((visual, index) => {
        const nextVisual = section.visuals?.[index + 1];
        const toFrame = visual.toFrame ?? nextVisual?.fromFrame ?? section.durationFrames;
        return frame >= visual.fromFrame && frame < toFrame;
      }) ?? section.visuals[section.visuals.length - 1]
    );
  }

  const switchFrame = section.switchFrame ?? 90;

  if (section.photoSrc && frame >= switchFrame) {
    return { src: section.photoSrc, kind: "photo", fromFrame: switchFrame };
  }

  if (section.imageSrc) {
    return { src: section.imageSrc, kind: "illustration", fromFrame: 0, toFrame: switchFrame };
  }

  return null;
};

const getVisualScale = (visual: ViralVisual, isHorizontal?: boolean) => {
  if (visual.kind === "photo" || isHorizontal) {
    return 1;
  }

  // Match perceived screen occupancy. Some illustration assets include wider
  // transparent margins or low-resolution thumbnails, so each asset needs a
  // visual-size correction instead of a uniform multiplier.
  if (visual.src.includes("illust_joushi")) {
    return 4.25;
  }

  if (visual.src.includes("illust_mushi")) {
    return 2.05;
  }

  if (visual.src.includes("illust_kazetooshi")) {
    return 2.08;
  }

  if (visual.src.includes("illust_jinzai")) {
    return 1.98;
  }

  return visual.src.includes("illust_") ? 1.38 : 1.18;
};

const collectVisualAssetSources = (props: ViralTemplateProps) => {
  return Array.from(
    new Set(
      [
        props.hook.imageSrc,
        ...(props.hook.callouts ?? []).map((callout) => callout.imageSrc),
        ...props.sections.flatMap((section) => [
          section.imageSrc,
          section.photoSrc,
          ...(section.visuals ?? []).map((visual) => visual.src),
        ]),
        props.cta.imageSrc1,
        props.cta.imageSrc2,
      ]
        .flat()
        .filter((src): src is string => Boolean(src)),
    ),
  );
};

const VisualAssetPreloader: React.FC<{ sources: string[] }> = ({ sources }) => {
  React.useEffect(() => {
    if (sources.length === 0) {
      return;
    }

    const handle = delayRender("Waiting for viral visual assets to load", {
      timeoutInMilliseconds: 180000,
    });

    Promise.all(
      sources.map(
        (src) =>
          new Promise<void>((resolve) => {
            const image = new Image();
            image.onload = () => resolve();
            image.onerror = () => {
              console.warn(`Failed to preload visual asset: ${src}`);
              resolve();
            };
            image.src = src;
          }),
      ),
    ).finally(() => continueRender(handle));
  }, [sources]);

  return null;
};

const StableImg: React.FC<React.ComponentProps<typeof Img>> = ({ style, src, onError, ...props }) => {
  const [failed, setFailed] = React.useState(false);

  if (failed) {
    return (
      <div
        style={{
          ...(style as React.CSSProperties),
          backgroundColor: "#F4F4F4",
        }}
      />
    );
  }

  return (
    <Img
      {...props}
      src={src}
      style={style}
      onError={(event) => {
        console.warn(`Failed to render visual asset: ${src}`);
        setFailed(true);
        onError?.(event);
      }}
    />
  );
};

const SubtitleTrack: React.FC<{
  subtitles: ViralSubtitleEntry[];
  isHorizontal?: boolean;
}> = ({ subtitles, isHorizontal }) => {
  const frame = useCurrentFrame();
  const subtitleLeadFrames = isHorizontal ? 0 : 6;
  const lookupFrame = frame + subtitleLeadFrames;
  const entry = subtitles.find((s) => lookupFrame >= s.from && lookupFrame < s.to);

  if (!entry || !entry.text) {
    return null;
  }

  const currentDuration = entry.to - entry.from;
  const progressInSegment = lookupFrame - entry.from;
  const opacity = interpolate(
    progressInSegment,
    [0, 3, currentDuration - 3, currentDuration],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const displayText = formatWrappedText(entry.text, {
    maxCharsPerLine: isHorizontal ? 22 : 11,
    preserveExistingLineBreaks: true,
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: isHorizontal ? "5%" : "35%",
        boxSizing: "border-box",
        opacity,
        pointerEvents: "none",
        zIndex: 100,
      }}
    >
      <div
        style={{
          ...SUBTITLE_STYLE,
          fontSize: isHorizontal ? 55 : 72,
          textAlign: "center",
          maxWidth: isHorizontal ? "95%" : "86%",
          whiteSpace: "pre-wrap",
          lineBreak: "strict",
          wordBreak: "keep-all",
          lineHeight: isHorizontal ? 1.2 : 1.16,
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
  const activeVisual = getActiveVisual(section, frame);
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
  const visualOpacity = activeVisual
    ? interpolate(frame - activeVisual.fromFrame, [0, 5], [0.68, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
      })
    : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF", alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: isHorizontal ? "10%" : "10%",
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
              : Math.min(88, 670 / getLongestLineLength(titleText)),
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
          top: isHorizontal ? "25%" : "27%",
          height: isHorizontal ? "60%" : "36%",
          display: "flex",
          justifyContent: "center",
          alignItems: isHorizontal ? "center" : "flex-start",
        }}
      >
        {activeVisual && (
          <div
            style={{
              position: "absolute",
              width: "100%",
              height: "100%",
              display: "flex",
              justifyContent: "center",
              alignItems: isHorizontal ? "center" : "flex-start",
	              opacity: visualOpacity,
		              transform: `scale(${imageScale * getVisualScale(activeVisual, isHorizontal)})`,
	              transformOrigin: "center top",
	            }}
          >
	            {activeVisual.kind === "photo" ? (
	              <StableImg
	                src={activeVisual.src}
	                style={{
	                  width: isHorizontal ? "60%" : "88%",
	                  height: "100%",
	                  aspectRatio: "16/9",
	                  objectFit: "cover",
	                  objectPosition: "center 58%",
	                  borderRadius: "8px",
	                  border: "3px solid #FFFFFF",
	                  boxShadow: "0 10px 28px rgba(0,0,0,0.12)",
	                }}
	              />
	            ) : (
	              <StableImg
	                src={activeVisual.src}
	                style={{
	                  maxHeight: "100%",
	                  maxWidth: isHorizontal ? "100%" : "94%",
	                  objectFit: "contain" as const,
	                }}
	              />
	            )}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const HookLayout: React.FC<{
  hook: ViralTemplateProps["hook"];
  isHorizontal?: boolean;
}> = ({ hook, isHorizontal }) => {
  const frame = useCurrentFrame();
  const activeCallout = [...(hook.callouts ?? [])]
    .reverse()
    .find((callout) => frame >= callout.fromFrame);
  const displayText = formatWrappedText(activeCallout?.text ?? hook.text, {
    maxCharsPerLine: isHorizontal ? 18 : 9,
    preserveExistingLineBreaks: true,
  });
  const imageSrc = activeCallout?.imageSrc ?? hook.imageSrc;
  const textScale = spring({
    fps: 30,
    frame: activeCallout ? frame - activeCallout.fromFrame : frame,
    config: { damping: 15, stiffness: 220 },
  });

  return (
    <>
	      <div
	        style={{
	          position: "absolute",
	          top: activeCallout ? (isHorizontal ? "36%" : "45%") : undefined,
	          bottom: activeCallout ? undefined : isHorizontal ? "5%" : "5%",
	          height: activeCallout ? (isHorizontal ? "48%" : "38%") : isHorizontal ? "60%" : "54%",
	          width: "100%",
	          display: "flex",
	          justifyContent: "center",
	          alignItems: activeCallout ? "flex-start" : "center",
	        }}
	      >
        {imageSrc && (
          <StableImg
            src={imageSrc}
	            style={{
	              maxHeight: "100%",
	              maxWidth: activeCallout ? (isHorizontal ? "84%" : "78%") : isHorizontal ? "90%" : "94%",
	              objectFit: "contain",
	              filter: "drop-shadow(0 10px 20px rgba(0,0,0,0.08))",
	            }}
          />
        )}
      </div>

      <div
	        style={{
	          position: "absolute",
	          top: activeCallout ? (isHorizontal ? "14%" : "31%") : isHorizontal ? "12%" : "20%",
	          width: "100%",
          display: "flex",
          justifyContent: "center",
          zIndex: 10,
          padding: isHorizontal ? "0 4%" : "0 5%",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
	            fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
	            fontSize: isHorizontal ? 95 : Math.min(activeCallout ? 130 : 136, 860 / getLongestLineLength(displayText)),
            fontWeight: 900,
            color: activeCallout ? "#000000" : "#ff2a2a",
            textAlign: "center",
            whiteSpace: "pre-wrap",
            lineBreak: "strict",
            wordBreak: "keep-all",
            lineHeight: isHorizontal ? 1.2 : 1.05,
            letterSpacing: 0,
            transform: `scale(${Math.min(1, 0.92 + textScale * 0.08)})`,
            textShadow: "0 0 15px white, 0 0 15px white",
          }}
        >
          {displayText}
        </div>
      </div>
    </>
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
        <StableImg
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
  sfx = [],
  backgroundColor = "#FAFAFA",
  isHorizontal = false,
}) => {
  const visualAssetSources = React.useMemo(
    () => collectVisualAssetSources({ totalFrames, audioSrc, subtitles, hook, sections, cta, sfx, backgroundColor, isHorizontal }),
    [audioSrc, backgroundColor, cta, hook, isHorizontal, sections, sfx, subtitles, totalFrames],
  );

  return (
    <AbsoluteFill style={{ background: backgroundColor }}>
      <VisualAssetPreloader sources={visualAssetSources} />

      <Sequence name="Hook" from={0} durationInFrames={hook.durationFrames}>
        <HookLayout hook={hook} isHorizontal={isHorizontal} />
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

      {sfx.map((cue, index) => (
        <Sequence
          key={`${cue.src}-${cue.fromFrame}-${index}`}
          name={`SFX ${index + 1}`}
          from={cue.fromFrame}
          durationInFrames={cue.durationFrames ?? totalFrames - cue.fromFrame}
        >
          <Audio src={cue.src} volume={cue.volume ?? 0.32} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
