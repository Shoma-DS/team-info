import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { Hook } from "../components/Hook";
import {
  ImageScene,
  type CameraMotionProfile,
  type CameraMotionType,
} from "../components/ImageScene";
import {
  VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
  useViralAdultAffiliateFont,
} from "../fonts";
import { splitDisplayLines } from "../../textLayout";

const motionTypes = [
  "zoom_in",
  "zoom_out",
  "pan_right",
  "pan_left",
  "tilt_up",
  "tilt_down",
  "shake",
  "static",
] as const satisfies readonly CameraMotionType[];

const motionProfiles = [
  "standard",
  "gentle",
  "still",
] as const satisfies readonly CameraMotionProfile[];

const sceneSchema = z.object({
  label: z.string().optional(),
  from: z.number().int().min(0),
  to: z.number().int().min(1),
  src: z.string().min(1),
  motionType: z.enum(motionTypes),
  motionProfile: z.enum(motionProfiles),
  motionIntensity: z.number().min(0).max(2),
  originX: z.number().min(0).max(1),
  originY: z.number().min(0).max(1),
  baseScale: z.number().min(0.5).max(2),
  cropXPercent: z.number().min(-50).max(50),
  cropYPercent: z.number().min(-50).max(50),
  flashOnEnter: z.boolean().optional(),
});

const subtitleSchema = z.object({
  label: z.string().optional(),
  from: z.number().int().min(0),
  to: z.number().int().min(1),
  text: z.string(),
  fontSize: z.number().int().min(24).max(240).optional(),
  xPercent: z.number().min(0).max(100).optional(),
  yPercent: z.number().min(0).max(100).optional(),
  maxWidthPercent: z.number().min(20).max(100).optional(),
  lineGap: z.number().min(0).max(40).optional(),
  lineColors: z.array(z.string()).max(6).optional(),
});

const styleSchema = z.object({
  textColor: z.string(),
  strokeColor: z.string(),
  outerStrokeColor: z.string(),
  dropShadow: z.string(),
  subtitleFontSize: z.number().int().min(24).max(240),
  nameCardFontSize: z.number().int().min(24).max(240),
  subtitleXPercent: z.number().min(0).max(100),
  subtitleYPercent: z.number().min(0).max(100),
  subtitleMaxWidthPercent: z.number().min(20).max(100),
  subtitleLineGap: z.number().min(0).max(40),
  subtitleLineHeight: z.number().min(0.8).max(2),
  subtitleEnterScaleFrom: z.number().min(0.1).max(2),
  subtitleFadeInFrames: z.number().int().min(1).max(30),
  strokeWidthPx: z.number().min(0).max(20),
  outerStrokeWidthPx: z.number().min(0).max(40),
  nameCardOuterStrokeWidthPx: z.number().min(0).max(40),
  hookFontSize: z.number().int().min(24).max(240),
  hookPaddingTopPercent: z.number().min(0).max(100),
  hookLineColors: z.array(z.string()).min(1).max(6),
  nameLineColors: z.array(z.string()).min(1).max(6),
  flashOpacity: z.number().min(0).max(1),
});

export const viralStudioEditorSchema = z.object({
  audioSrc: z.string().min(1),
  hookDurationFrames: z.number().int().min(1),
  fadeFrames: z.number().int().min(0).max(60),
  flashDurationFrames: z.number().int().min(0).max(30),
  scenes: z.array(sceneSchema).min(1),
  subtitles: z.array(subtitleSchema).min(1),
  style: styleSchema,
});

export type ViralStudioEditorProps = z.infer<typeof viralStudioEditorSchema>;

type SceneEntry = ViralStudioEditorProps["scenes"][number];
type SubtitleEntry = ViralStudioEditorProps["subtitles"][number];

const isNameCard = (text: string) => /^[0-9]+\./.test(text.trim());

const sortByTimeline = <T extends { from: number; to: number }>(entries: T[]): T[] => {
  return [...entries].sort((a, b) => a.from - b.from || a.to - b.to);
};

const getCurrentSceneIndex = (entries: SceneEntry[], frame: number) => {
  let fallback = 0;

  for (let i = 0; i < entries.length; i += 1) {
    const entry = entries[i];

    if (frame >= entry.from) {
      fallback = i;
    }

    if (frame >= entry.from && frame < entry.to) {
      return i;
    }

    if (frame < entry.from) {
      return fallback;
    }
  }

  return fallback;
};

const SceneImage: React.FC<{ entry: SceneEntry }> = ({ entry }) => {
  return (
    <ImageScene
      src={staticFile(entry.src)}
      motionType={entry.motionType}
      motionProfile={entry.motionProfile}
      motionIntensity={entry.motionIntensity}
      originX={entry.originX}
      originY={entry.originY}
      baseScale={entry.baseScale}
      cropXPercent={entry.cropXPercent}
      cropYPercent={entry.cropYPercent}
    />
  );
};

const ImageSceneTrack: React.FC<{
  scenes: SceneEntry[];
  fadeFrames: number;
}> = ({ scenes, fadeFrames }) => {
  const frame = useCurrentFrame();
  const currentIndex = getCurrentSceneIndex(scenes, frame);
  const current = scenes[currentIndex] ?? scenes[scenes.length - 1];
  const previous = currentIndex > 0 ? scenes[currentIndex - 1] : null;
  const relFrame = Math.max(0, frame - current.from);
  const shouldFade = previous !== null && fadeFrames > 0 && relFrame < fadeFrames;
  const fadeOpacity = shouldFade ? relFrame / fadeFrames : 1;

  return (
    <AbsoluteFill>
      {shouldFade && (
        <AbsoluteFill style={{ opacity: 1 - fadeOpacity }}>
          <SceneImage entry={previous} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ opacity: fadeOpacity }}>
        <SceneImage entry={current} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const SubtitleTrack: React.FC<{
  subtitles: SubtitleEntry[];
  style: ViralStudioEditorProps["style"];
  hookDurationFrames: number;
}> = ({ subtitles, style, hookDurationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (frame < hookDurationFrames) {
    return null;
  }

  const entry = subtitles.find((subtitle) => frame >= subtitle.from && frame < subtitle.to);
  if (!entry) {
    return null;
  }

  const relFrame = frame - entry.from;
  const progress = spring({
    fps,
    frame: relFrame,
    config: { damping: 14, stiffness: 180 },
  });
  const opacity = interpolate(relFrame, [0, style.subtitleFadeInFrames], [0, 1], {
    extrapolateRight: "clamp",
  });
  const scale = interpolate(progress, [0, 1], [style.subtitleEnterScaleFrom, 1]);
  const cardMode = isNameCard(entry.text);
  const lines = splitDisplayLines(entry.text, {
    maxCharsPerLine: 12,
    preserveExistingLineBreaks: true,
  });
  const lineColors = lines.map((_, index) => {
    if (entry.lineColors?.[index]) {
      return entry.lineColors[index];
    }

    if (cardMode) {
      return style.nameLineColors[index] ?? style.textColor;
    }

    return style.textColor;
  });
  const fontSize = entry.fontSize ?? (cardMode ? style.nameCardFontSize : style.subtitleFontSize);
  const outerStrokeWidth = cardMode
    ? style.nameCardOuterStrokeWidthPx
    : style.outerStrokeWidthPx;
  const xPercent = entry.xPercent ?? style.subtitleXPercent;
  const yPercent = entry.yPercent ?? style.subtitleYPercent;
  const maxWidthPercent = entry.maxWidthPercent ?? style.subtitleMaxWidthPercent;
  const lineGap = entry.lineGap ?? style.subtitleLineGap;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: `${yPercent}%`,
          left: `${xPercent}%`,
          transform: `translateX(-50%) scale(${scale})`,
          opacity,
          width: "100%",
          maxWidth: `${maxWidthPercent}%`,
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
            const sharedStyle = {
              fontFamily: VIRAL_ADULT_AFFILIATE_FONT_FAMILY,
              fontSize,
              fontWeight: 900 as const,
              lineHeight: style.subtitleLineHeight,
              whiteSpace: "pre-wrap" as const,
            };

            return (
              <div
                key={`${entry.from}-${index}-${line}`}
                style={{ position: "relative", marginTop: index === 0 ? 0 : lineGap }}
              >
                <div
                  style={{
                    ...sharedStyle,
                    color: style.outerStrokeColor,
                    WebkitTextStroke: `${outerStrokeWidth}px ${style.outerStrokeColor}`,
                    textShadow: style.dropShadow,
                  }}
                >
                  {line}
                </div>
                <div
                  style={{
                    ...sharedStyle,
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    textAlign: "center",
                    color: lineColors[index],
                    WebkitTextStroke: `${style.strokeWidthPx}px ${style.strokeColor}`,
                  }}
                >
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

const FlashTrack: React.FC<{
  scenes: SceneEntry[];
  flashDurationFrames: number;
  flashOpacity: number;
}> = ({ scenes, flashDurationFrames, flashOpacity }) => {
  const frame = useCurrentFrame();
  const isFlash = scenes.some((scene, index) => {
    if (index === 0 || !scene.flashOnEnter) {
      return false;
    }

    return frame >= scene.from && frame < scene.from + flashDurationFrames;
  });

  if (!isFlash) {
    return null;
  }

  return (
    <AbsoluteFill
      style={{ background: "white", opacity: flashOpacity, pointerEvents: "none" }}
    />
  );
};

export const EditableViralVideo: React.FC<ViralStudioEditorProps> = ({
  audioSrc,
  hookDurationFrames,
  fadeFrames,
  flashDurationFrames,
  scenes,
  subtitles,
  style,
}) => {
  useViralAdultAffiliateFont();

  const sortedScenes = sortByTimeline(scenes);
  const sortedSubtitles = sortByTimeline(subtitles);
  const hookEntry = sortedSubtitles[0];

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Sequence name="背景画像">
        <ImageSceneTrack scenes={sortedScenes} fadeFrames={fadeFrames} />
      </Sequence>

      <Sequence name="フック テキスト" durationInFrames={hookDurationFrames}>
        <Hook
          hookType="statement"
          text={hookEntry?.text ?? ""}
          startFrame={hookEntry?.from ?? 0}
          endFrame={hookDurationFrames}
          durationFrames={hookDurationFrames}
          fontFamily={VIRAL_ADULT_AFFILIATE_FONT_FAMILY}
          fontSize={style.hookFontSize}
          strokeWidth={`${style.strokeWidthPx}px`}
          strokeColor={style.strokeColor}
          outerStrokeWidth={`${style.outerStrokeWidthPx}px`}
          textShadow={style.dropShadow}
          lineColors={style.hookLineColors}
          paddingTop={`${style.hookPaddingTopPercent}%`}
        />
      </Sequence>

      <Sequence name="フラッシュ 演出">
        <FlashTrack
          scenes={sortedScenes}
          flashDurationFrames={flashDurationFrames}
          flashOpacity={style.flashOpacity}
        />
      </Sequence>

      <Sequence name="字幕">
        <SubtitleTrack
          subtitles={sortedSubtitles}
          style={style}
          hookDurationFrames={hookDurationFrames}
        />
      </Sequence>

      <Sequence name="音声 ナレーション">
        <Audio src={staticFile(audioSrc)} volume={1.0} />
      </Sequence>
    </AbsoluteFill>
  );
};
