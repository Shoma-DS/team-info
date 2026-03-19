import { Player, type PlayerRef } from "@remotion/player";
import React, {
  startTransition,
  useDeferredValue,
  useEffect,
  useRef,
  useState,
} from "react";
import { AbsoluteFill } from "remotion";
import {
  EditableViralVideo,
  viralStudioEditorSchema,
  type ViralStudioEditorProps,
} from "./EditableViralVideo";
import {
  getViralEditorPresetById,
  type ViralEditorPreset,
  type ViralEditorPresetId,
  viralEditorPresets,
} from "./presets";

type SceneClip = ViralStudioEditorProps["scenes"][number] & { clipId: string };
type SubtitleClip = ViralStudioEditorProps["subtitles"][number] & { clipId: string };
type EditableTrack = "scenes" | "subtitles";

type EditorState = Omit<ViralStudioEditorProps, "scenes" | "subtitles"> & {
  scenes: SceneClip[];
  subtitles: SubtitleClip[];
};

type Selection = {
  track: EditableTrack;
  clipId: string;
};

type DragState = {
  track: EditableTrack;
  clipId: string;
  mode: "move" | "resize-start" | "resize-end";
  startClientX: number;
  originalFrom: number;
  originalTo: number;
};

type ViralClipEditorProps = {
  initialPresetId?: ViralEditorPresetId;
};

const TRACK_HEADER_WIDTH = 124;
const TOOL_FONT =
  '"Avenir Next", "Hiragino Sans", "Yu Gothic", "YuGothic", "Meiryo", sans-serif';
const MONO_FONT =
  '"SFMono-Regular", "Menlo", "Monaco", "Consolas", "Liberation Mono", monospace';

let clipIdCounter = 0;

const nextClipId = () => {
  clipIdCounter += 1;
  return `clip-${clipIdCounter}`;
};

const sortClips = <T extends { from: number; to: number }>(clips: T[]): T[] => {
  return [...clips].sort((a, b) => a.from - b.from || a.to - b.to);
};

const clamp = (value: number, min: number, max: number) => {
  return Math.min(Math.max(value, min), max);
};

const withClipIds = (
  props: ViralStudioEditorProps,
): EditorState => {
  return {
    ...props,
    scenes: sortClips(props.scenes).map((clip) => ({
      ...clip,
      clipId: nextClipId(),
    })),
    subtitles: sortClips(props.subtitles).map((clip) => ({
      ...clip,
      clipId: nextClipId(),
    })),
  };
};

const omitClipId = <T extends { clipId: string }>(clip: T): Omit<T, "clipId"> => {
  const { clipId, ...rest } = clip;
  void clipId;
  return rest;
};

const stripClipIds = (state: EditorState): ViralStudioEditorProps => {
  return {
    ...state,
    scenes: sortClips(state.scenes.map((clip) => omitClipId(clip))),
    subtitles: sortClips(state.subtitles.map((clip) => omitClipId(clip))),
  };
};

const loadEditorState = (preset: ViralEditorPreset): EditorState => {
  if (typeof window === "undefined") {
    return withClipIds(preset.props);
  }

  const raw = window.localStorage.getItem(preset.storageKey);
  if (!raw) {
    return withClipIds(preset.props);
  }

  try {
    const parsed = JSON.parse(raw);
    const result = viralStudioEditorSchema.safeParse(parsed);
    if (!result.success) {
      return withClipIds(preset.props);
    }

    return withClipIds(result.data);
  } catch {
    return withClipIds(preset.props);
  }
};

const saveEditorState = (preset: ViralEditorPreset, state: EditorState) => {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(
    preset.storageKey,
    JSON.stringify(stripClipIds(state)),
  );
};

const getClipBySelection = (
  state: EditorState,
  selection: Selection | null,
) => {
  if (!selection) {
    return null;
  }

  const track = selection.track === "scenes" ? state.scenes : state.subtitles;
  return track.find((clip) => clip.clipId === selection.clipId) ?? null;
};

const updateClip = <T extends { clipId: string; from: number; to: number }>(
  clips: T[],
  clipId: string,
  updater: (clip: T) => T,
): T[] => {
  return sortClips(
    clips.map((clip) => {
      if (clip.clipId !== clipId) {
        return clip;
      }

      return updater(clip);
    }),
  );
};

const replaceSelectionClip = (
  state: EditorState,
  selection: Selection,
  updater: (clip: SceneClip | SubtitleClip) => SceneClip | SubtitleClip,
): EditorState => {
  if (selection.track === "scenes") {
    return {
      ...state,
      scenes: updateClip(state.scenes, selection.clipId, (clip) => {
        return updater(clip) as SceneClip;
      }),
    };
  }

  return {
    ...state,
    subtitles: updateClip(state.subtitles, selection.clipId, (clip) => {
      return updater(clip) as SubtitleClip;
    }),
  };
};

const applyDrag = (
  state: EditorState,
  dragState: DragState,
  deltaFrames: number,
  durationInFrames: number,
): EditorState => {
  const clipDuration = dragState.originalTo - dragState.originalFrom;

  return replaceSelectionClip(
    state,
    { track: dragState.track, clipId: dragState.clipId },
    (clip) => {
      if (dragState.mode === "move") {
        const nextFrom = clamp(
          dragState.originalFrom + deltaFrames,
          0,
          Math.max(0, durationInFrames - clipDuration),
        );
        return {
          ...clip,
          from: nextFrom,
          to: nextFrom + clipDuration,
        };
      }

      if (dragState.mode === "resize-start") {
        return {
          ...clip,
          from: clamp(
            dragState.originalFrom + deltaFrames,
            0,
            dragState.originalTo - 1,
          ),
        };
      }

      return {
        ...clip,
        to: clamp(
          dragState.originalTo + deltaFrames,
          dragState.originalFrom + 1,
          durationInFrames,
        ),
      };
    },
  );
};

const analyzeTrack = (clips: { from: number; to: number }[]) => {
  const sorted = sortClips(clips);
  let overlaps = 0;
  let gaps = 0;

  for (let i = 1; i < sorted.length; i += 1) {
    const prev = sorted[i - 1];
    const current = sorted[i];

    if (current.from < prev.to) {
      overlaps += 1;
    }

    if (current.from > prev.to) {
      gaps += 1;
    }
  }

  return { overlaps, gaps };
};

const formatTime = (frame: number, fps: number) => {
  return `${(frame / fps).toFixed(2)}s`;
};

const getFrameStep = (zoom: number) => {
  if (zoom <= 1.5) {
    return 150;
  }

  if (zoom <= 2.5) {
    return 90;
  }

  if (zoom <= 4) {
    return 60;
  }

  return 30;
};

const getSceneLabel = (clip: SceneClip) => {
  if (clip.label) {
    return clip.label;
  }

  const fileName = clip.src.split("/").pop() ?? clip.src;
  return fileName.replace(/\.[^.]+$/, "");
};

const getSubtitleLabel = (clip: SubtitleClip) => {
  if (clip.label) {
    return clip.label;
  }

  return clip.text.split("\n").join(" ").slice(0, 22) || "字幕";
};

const buttonStyle = (tone: "neutral" | "accent" | "warn" = "neutral"): React.CSSProperties => {
  const background =
    tone === "accent"
      ? "linear-gradient(135deg, #ffb300 0%, #ff7a18 100%)"
      : tone === "warn"
        ? "linear-gradient(135deg, #ff5f6d 0%, #ffc371 100%)"
        : "rgba(255,255,255,0.08)";

  const color = tone === "neutral" ? "#f5f1e8" : "#121212";

  return {
    appearance: "none",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 12,
    background,
    color,
    cursor: "pointer",
    padding: "10px 14px",
    fontSize: 15,
    fontWeight: 700,
    fontFamily: TOOL_FONT,
  };
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "rgba(12, 15, 24, 0.75)",
  color: "#f4f1e8",
  padding: "10px 12px",
  fontSize: 15,
  fontFamily: TOOL_FONT,
  boxSizing: "border-box",
};

const panelStyle: React.CSSProperties = {
  borderRadius: 28,
  border: "1px solid rgba(255,255,255,0.08)",
  background:
    "linear-gradient(180deg, rgba(18, 22, 36, 0.94) 0%, rgba(9, 12, 21, 0.96) 100%)",
  boxShadow: "0 28px 60px rgba(0,0,0,0.35)",
};

const LabeledField: React.FC<{
  label: string;
  mono?: boolean;
  children: React.ReactNode;
}> = ({ label, mono = false, children }) => {
  return (
    <label
      style={{
        display: "grid",
        gap: 8,
        fontSize: 13,
        fontWeight: 700,
        color: "#cfc7b6",
        letterSpacing: "0.03em",
        fontFamily: mono ? MONO_FONT : TOOL_FONT,
      }}
    >
      {label}
      {children}
    </label>
  );
};

const MetaPill: React.FC<{ label: string; value: string }> = ({ label, value }) => {
  return (
    <div
      style={{
        borderRadius: 14,
        padding: "10px 12px",
        background: "rgba(255,255,255,0.05)",
        border: "1px solid rgba(255,255,255,0.08)",
        display: "grid",
        gap: 4,
      }}
    >
      <div
        style={{
          fontSize: 11,
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          color: "#998c73",
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 16, fontWeight: 700, color: "#f4f1e8" }}>{value}</div>
    </div>
  );
};

export const ViralClipEditor: React.FC<ViralClipEditorProps> = ({
  initialPresetId = viralEditorPresets[0].id,
}) => {
  // <Player> をマウント後にのみレンダリング。初期レンダリング中に isPlayer フラグが
  // グローバルに設定されると Remotion Studio の getInputProps() と衝突するため。
  const [isMounted, setIsMounted] = useState(false);
  useEffect(() => { setIsMounted(true); }, []);

  const [presetId, setPresetId] = useState<ViralEditorPresetId>(initialPresetId);
  const preset = getViralEditorPresetById(presetId);
  const [editorState, setEditorState] = useState<EditorState>(() => loadEditorState(preset));
  const [selection, setSelection] = useState<Selection | null>(null);
  const [dragState, setDragState] = useState<DragState | null>(null);
  const [timelineWidth, setTimelineWidth] = useState(880);
  const [zoom, setZoom] = useState(1.35);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");

  const playerRef = useRef<PlayerRef>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const timelineViewportRef = useRef<HTMLDivElement>(null);

  const previewProps = stripClipIds(editorState);
  const deferredPreviewProps = useDeferredValue(previewProps);
  const timelineViewportContentWidth = Math.max(timelineWidth - TRACK_HEADER_WIDTH, 320);
  const pxPerFrame = Math.max(
    0.4,
    (timelineViewportContentWidth / preset.durationInFrames) * zoom,
  );
  const timelineFramesWidth = preset.durationInFrames * pxPerFrame;
  const timelineContentWidth = TRACK_HEADER_WIDTH + timelineFramesWidth;
  const selectedClip = getClipBySelection(editorState, selection);
  const sceneStats = analyzeTrack(editorState.scenes);
  const subtitleStats = analyzeTrack(editorState.subtitles);

  useEffect(() => {
    saveEditorState(preset, editorState);
  }, [editorState, preset]);

  useEffect(() => {
    if (!statusMessage || typeof window === "undefined") {
      return;
    }

    const timeout = window.setTimeout(() => {
      setStatusMessage("");
    }, 2200);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [statusMessage]);

  useEffect(() => {
    const viewport = timelineViewportRef.current;
    if (!viewport || typeof ResizeObserver === "undefined") {
      return;
    }

    const observer = new ResizeObserver((entries) => {
      const [entry] = entries;
      if (!entry) {
        return;
      }

      setTimelineWidth(entry.contentRect.width);
    });

    observer.observe(viewport);

    return () => {
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    const player = playerRef.current;
    if (!player) {
      return;
    }

    const syncFrame = (event: { detail: { frame: number } }) => {
      setCurrentFrame(event.detail.frame);
    };

    player.addEventListener("frameupdate", syncFrame);
    player.addEventListener("seeked", syncFrame);
    setCurrentFrame(player.getCurrentFrame());

    return () => {
      player.removeEventListener("frameupdate", syncFrame);
      player.removeEventListener("seeked", syncFrame);
    };
  }, [preset.id, deferredPreviewProps]);

  useEffect(() => {
    if (!dragState) {
      return;
    }

    const handlePointerMove = (event: PointerEvent) => {
      const deltaFrames = Math.round(
        (event.clientX - dragState.startClientX) / pxPerFrame,
      );

      setEditorState((prev) => {
        return applyDrag(prev, dragState, deltaFrames, preset.durationInFrames);
      });
    };

    const handlePointerUp = () => {
      setDragState(null);
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };
  }, [dragState, pxPerFrame, preset.durationInFrames]);

  const seekToFrame = (frame: number) => {
    const nextFrame = clamp(Math.round(frame), 0, preset.durationInFrames - 1);
    playerRef.current?.seekTo(nextFrame);
    setCurrentFrame(nextFrame);
  };

  const updateSelection = (
    updater: (clip: SceneClip | SubtitleClip) => SceneClip | SubtitleClip,
  ) => {
    if (!selection) {
      return;
    }

    setEditorState((prev) => replaceSelectionClip(prev, selection, updater));
  };

  const splitSelectedClip = () => {
    if (!selection || !selectedClip) {
      setStatusMessage("分割するクリップを選択してください");
      return;
    }

    const splitFrame = clamp(currentFrame, selectedClip.from + 1, selectedClip.to - 1);
    if (splitFrame <= selectedClip.from || splitFrame >= selectedClip.to) {
      setStatusMessage("再生ヘッドがクリップ内にありません");
      return;
    }

    setEditorState((prev) => {
      if (selection.track === "scenes") {
        const updated = prev.scenes.flatMap((clip) => {
          if (clip.clipId !== selection.clipId) {
            return [clip];
          }

          const firstHalf: SceneClip = { ...clip, to: splitFrame };
          const secondHalf: SceneClip = {
            ...clip,
            clipId: nextClipId(),
            from: splitFrame,
            label: clip.label ? `${clip.label} B` : undefined,
          };
          return [firstHalf, secondHalf];
        });

        return { ...prev, scenes: sortClips(updated) };
      }

      const updated = prev.subtitles.flatMap((clip) => {
        if (clip.clipId !== selection.clipId) {
          return [clip];
        }

        const firstHalf: SubtitleClip = { ...clip, to: splitFrame };
        const secondHalf: SubtitleClip = {
          ...clip,
          clipId: nextClipId(),
          from: splitFrame,
          label: clip.label ? `${clip.label} B` : undefined,
        };
        return [firstHalf, secondHalf];
      });

      return { ...prev, subtitles: sortClips(updated) };
    });

    setStatusMessage("再生ヘッド位置で分割しました");
  };

  const deleteSelectedClip = () => {
    if (!selection) {
      return;
    }

    setEditorState((prev) => {
      if (selection.track === "scenes" && prev.scenes.length > 1) {
        return {
          ...prev,
          scenes: prev.scenes.filter((clip) => clip.clipId !== selection.clipId),
        };
      }

      if (selection.track === "subtitles" && prev.subtitles.length > 1) {
        return {
          ...prev,
          subtitles: prev.subtitles.filter((clip) => clip.clipId !== selection.clipId),
        };
      }

      return prev;
    });

    setSelection(null);
  };

  const resetToBuiltIn = () => {
    startTransition(() => {
      setEditorState(withClipIds(preset.props));
      setSelection(null);
      setCurrentFrame(0);
    });
    setStatusMessage("プリセットの初期状態に戻しました");
  };

  const copyJson = async () => {
    if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) {
      setStatusMessage("この環境ではクリップボードにコピーできません");
      return;
    }

    await navigator.clipboard.writeText(
      JSON.stringify(stripClipIds(editorState), null, 2),
    );
    setStatusMessage("JSON をクリップボードへコピーしました");
  };

  const exportJson = () => {
    if (typeof document === "undefined") {
      return;
    }

    const blob = new Blob([JSON.stringify(stripClipIds(editorState), null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${preset.storageKey}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    setStatusMessage("JSON をダウンロードしました");
  };

  const importJson = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const text = await file.text();

    try {
      const parsed = JSON.parse(text);
      const result = viralStudioEditorSchema.safeParse(parsed);
      if (!result.success) {
        setStatusMessage("JSON の形式が違います");
        return;
      }

      startTransition(() => {
        setEditorState(withClipIds(result.data));
        setSelection(null);
      });
      setStatusMessage("JSON を読み込みました");
    } catch {
      setStatusMessage("JSON の読み込みに失敗しました");
    } finally {
      event.target.value = "";
    }
  };

  const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const nextPresetId = event.target.value as ViralEditorPresetId;
    const nextPreset = getViralEditorPresetById(nextPresetId);
    startTransition(() => {
      setPresetId(nextPresetId);
      setEditorState(loadEditorState(nextPreset));
      setSelection(null);
      setCurrentFrame(0);
    });
  };

  const startDrag = (
    event: React.PointerEvent<HTMLDivElement>,
    track: EditableTrack,
    clipId: string,
    mode: DragState["mode"],
    from: number,
    to: number,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    playerRef.current?.pause();
    setSelection({ track, clipId });
    setDragState({
      track,
      clipId,
      mode,
      startClientX: event.clientX,
      originalFrom: from,
      originalTo: to,
    });
  };

  const handleTimelinePointerDown = (
    event: React.PointerEvent<HTMLDivElement>,
  ) => {
    const viewport = timelineViewportRef.current;
    if (!viewport) {
      return;
    }

    const frame =
      (
        event.clientX -
        viewport.getBoundingClientRect().left +
        viewport.scrollLeft -
        TRACK_HEADER_WIDTH
      ) /
      pxPerFrame;
    seekToFrame(frame);
  };

  const selectedIsScene = selection?.track === "scenes";
  const selectedIsSubtitle = selection?.track === "subtitles";
  const currentScene = selectedIsScene ? (selectedClip as SceneClip | null) : null;
  const currentSubtitle = selectedIsSubtitle ? (selectedClip as SubtitleClip | null) : null;

  return (
    <AbsoluteFill
      style={{
        fontFamily: TOOL_FONT,
        color: "#f4f1e8",
        background:
          "radial-gradient(circle at top left, rgba(244,132,66,0.18) 0%, rgba(20,24,34,0) 32%), linear-gradient(135deg, #0b0e14 0%, #111827 55%, #0c1018 100%)",
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="application/json,.json"
        style={{ display: "none" }}
        onChange={importJson}
      />

      <div
        style={{
          display: "grid",
          gridTemplateRows: "88px 1fr",
          height: "100%",
          padding: 24,
          boxSizing: "border-box",
          gap: 20,
        }}
      >
        <div
          style={{
            ...panelStyle,
            display: "grid",
            gridTemplateColumns: "280px 1fr auto",
            gap: 18,
            alignItems: "center",
            padding: "18px 22px",
          }}
        >
          <div style={{ display: "grid", gap: 6 }}>
            <div
              style={{
                fontSize: 12,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                color: "#9f8f72",
              }}
            >
              Viral Clip Editor
            </div>
            <div style={{ fontSize: 26, fontWeight: 800 }}>{preset.label}</div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "240px 160px 160px 1fr",
              gap: 12,
              alignItems: "center",
            }}
          >
            <LabeledField label="プリセット">
              <select value={preset.id} onChange={handlePresetChange} style={inputStyle}>
                {viralEditorPresets.map((item) => {
                  return (
                    <option key={item.id} value={item.id}>
                      {item.label}
                    </option>
                  );
                })}
              </select>
            </LabeledField>

            <LabeledField label="ズーム">
              <input
                type="range"
                min={1}
                max={6}
                step={0.05}
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
              />
            </LabeledField>

            <LabeledField label="再生ヘッド" mono>
              <input
                type="number"
                value={currentFrame}
                min={0}
                max={preset.durationInFrames - 1}
                onChange={(event) => seekToFrame(Number(event.target.value))}
                style={inputStyle}
              />
            </LabeledField>

            <div
              style={{
                display: "flex",
                gap: 10,
                justifyContent: "flex-end",
                alignItems: "end",
              }}
            >
              <button type="button" style={buttonStyle()} onClick={() => playerRef.current?.toggle()}>
                再生 / 停止
              </button>
              <button type="button" style={buttonStyle("accent")} onClick={splitSelectedClip}>
                選択中を分割
              </button>
              <button type="button" style={buttonStyle()} onClick={copyJson}>
                JSON コピー
              </button>
              <button type="button" style={buttonStyle()} onClick={exportJson}>
                JSON 書き出し
              </button>
              <button
                type="button"
                style={buttonStyle()}
                onClick={() => fileInputRef.current?.click()}
              >
                JSON 読み込み
              </button>
            </div>
          </div>

          <div
            style={{
              minWidth: 170,
              textAlign: "right",
              color: statusMessage ? "#ffcb77" : "#8f95a3",
              fontSize: 14,
              fontWeight: 700,
            }}
          >
            {statusMessage || "autosave: localStorage"}
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "560px minmax(0, 1fr) 360px",
            gap: 20,
            minHeight: 0,
          }}
        >
          <div style={{ ...panelStyle, padding: 20, display: "grid", gridTemplateRows: "1fr auto", gap: 16 }}>
            <div
              style={{
                borderRadius: 22,
                overflow: "hidden",
                background:
                  "linear-gradient(180deg, rgba(6,8,13,0.95) 0%, rgba(16,20,30,0.95) 100%)",
                border: "1px solid rgba(255,255,255,0.08)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: 20,
              }}
            >
              {isMounted ? (
                <Player
                  key={preset.id}
                  ref={playerRef}
                  component={EditableViralVideo}
                  inputProps={deferredPreviewProps}
                  durationInFrames={preset.durationInFrames}
                  fps={preset.fps}
                  compositionHeight={preset.height}
                  compositionWidth={preset.width}
                  style={{
                    width: 432,
                    height: 768,
                    borderRadius: 26,
                    overflow: "hidden",
                    boxShadow: "0 28px 60px rgba(0,0,0,0.45)",
                    background: "#000",
                  }}
                  controls={false}
                  clickToPlay={false}
                  autoPlay={false}
                  acknowledgeRemotionLicense
                />
              ) : (
                <div style={{ width: 432, height: 768, borderRadius: 26, background: "#000" }} />
              )}
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                gap: 10,
              }}
            >
              <MetaPill label="Current" value={`${currentFrame}f / ${formatTime(currentFrame, preset.fps)}`} />
              <MetaPill
                label="Scene Track"
                value={`gap ${sceneStats.gaps} / overlap ${sceneStats.overlaps}`}
              />
              <MetaPill
                label="Subtitle Track"
                value={`gap ${subtitleStats.gaps} / overlap ${subtitleStats.overlaps}`}
              />
              <MetaPill
                label="Selected"
                value={
                  selectedClip
                    ? `${selectedClip.from}-${selectedClip.to}`
                    : "none"
                }
              />
            </div>
          </div>

          <div
            style={{
              ...panelStyle,
              display: "grid",
              gridTemplateRows: "auto 1fr auto",
              minHeight: 0,
              padding: 18,
              gap: 14,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: 12,
                    letterSpacing: "0.14em",
                    textTransform: "uppercase",
                    color: "#948a75",
                  }}
                >
                  Drag Timeline
                </div>
                <div style={{ fontSize: 22, fontWeight: 800 }}>
                  split / move / trim
                </div>
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button type="button" style={buttonStyle()} onClick={() => seekToFrame(0)}>
                  先頭へ
                </button>
                <button type="button" style={buttonStyle("warn")} onClick={deleteSelectedClip}>
                  選択を削除
                </button>
                <button type="button" style={buttonStyle()} onClick={resetToBuiltIn}>
                  初期化
                </button>
              </div>
            </div>

            <div
              ref={timelineViewportRef}
              style={{
                position: "relative",
                overflowX: "auto",
                overflowY: "hidden",
                borderRadius: 20,
                border: "1px solid rgba(255,255,255,0.08)",
                background:
                  "linear-gradient(180deg, rgba(9,12,18,0.94) 0%, rgba(14,18,27,0.96) 100%)",
              }}
              onPointerDown={handleTimelinePointerDown}
            >
              <div
                style={{
                  position: "relative",
                  width: timelineContentWidth,
                  minHeight: 372,
                  paddingBottom: 24,
                }}
              >
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: `${TRACK_HEADER_WIDTH}px 1fr`,
                    background: "rgba(10,12,18,0.92)",
                    backdropFilter: "blur(14px)",
                    borderBottom: "1px solid rgba(255,255,255,0.06)",
                  }}
                >
                  <div
                    style={{
                      borderRight: "1px solid rgba(255,255,255,0.08)",
                      padding: "14px 12px",
                      fontSize: 12,
                      letterSpacing: "0.14em",
                      textTransform: "uppercase",
                      color: "#97886c",
                    }}
                  >
                    ruler
                  </div>
                  <div style={{ position: "relative", height: 48 }}>
                    {Array.from({
                      length: Math.ceil(preset.durationInFrames / getFrameStep(zoom)) + 1,
                    }).map((_, index) => {
                      const frame = index * getFrameStep(zoom);
                      const left = frame * pxPerFrame;
                      return (
                        <div
                          key={frame}
                          style={{
                            position: "absolute",
                            top: 0,
                            left,
                            bottom: 0,
                            width: 1,
                            background: "rgba(255,255,255,0.08)",
                          }}
                        >
                          <div
                            style={{
                              position: "absolute",
                              top: 10,
                              left: 8,
                              fontSize: 11,
                              color: "#9e9ca5",
                              fontFamily: MONO_FONT,
                              whiteSpace: "nowrap",
                            }}
                          >
                            {frame}f
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {[
                  {
                    key: "scenes" as const,
                    title: "背景画像",
                    color: "linear-gradient(135deg, #3fb8af 0%, #4fd3c4 100%)",
                    clips: editorState.scenes,
                  },
                  {
                    key: "subtitles" as const,
                    title: "字幕",
                    color: "linear-gradient(135deg, #ffaf45 0%, #ff5f6d 100%)",
                    clips: editorState.subtitles,
                  },
                ].map((track) => {
                  return (
                    <div
                      key={track.key}
                      style={{
                        position: "relative",
                        display: "grid",
                        gridTemplateColumns: `${TRACK_HEADER_WIDTH}px 1fr`,
                        minHeight: 142,
                        borderBottom: "1px solid rgba(255,255,255,0.06)",
                      }}
                    >
                      <div
                        style={{
                          padding: "20px 14px",
                          borderRight: "1px solid rgba(255,255,255,0.08)",
                          display: "grid",
                          alignContent: "start",
                          gap: 10,
                          background: "rgba(255,255,255,0.02)",
                        }}
                      >
                        <div style={{ fontSize: 18, fontWeight: 800 }}>{track.title}</div>
                        <div
                          style={{
                            fontSize: 12,
                            color: "#9a96a4",
                            fontFamily: MONO_FONT,
                          }}
                        >
                          {track.clips.length} clips
                        </div>
                      </div>
                      <div style={{ position: "relative", minHeight: 142 }}>
                        {Array.from({
                          length: Math.ceil(preset.durationInFrames / getFrameStep(zoom)) + 1,
                        }).map((_, index) => {
                          const frame = index * getFrameStep(zoom);
                          return (
                            <div
                              key={`${track.key}-${frame}`}
                              style={{
                                position: "absolute",
                                top: 0,
                                bottom: 0,
                                left: frame * pxPerFrame,
                                width: 1,
                                background: "rgba(255,255,255,0.06)",
                              }}
                            />
                          );
                        })}

                        {track.clips.map((clip) => {
                          const left = clip.from * pxPerFrame;
                          const width = Math.max((clip.to - clip.from) * pxPerFrame, 12);
                          const isSelected =
                            selection?.track === track.key &&
                            selection.clipId === clip.clipId;
                          const label =
                            track.key === "scenes"
                              ? getSceneLabel(clip as SceneClip)
                              : getSubtitleLabel(clip as SubtitleClip);

                          return (
                            <div
                              key={clip.clipId}
                              style={{
                                position: "absolute",
                                top: 26,
                                left,
                                width,
                                height: 88,
                                borderRadius: 16,
                                background: track.color,
                                border: isSelected
                                  ? "2px solid rgba(255,255,255,0.92)"
                                  : "1px solid rgba(255,255,255,0.2)",
                                boxShadow: isSelected
                                  ? "0 0 0 3px rgba(255,255,255,0.14)"
                                  : "none",
                                overflow: "hidden",
                                cursor: dragState ? "grabbing" : "grab",
                              }}
                              onPointerDown={(event) =>
                                startDrag(
                                  event,
                                  track.key,
                                  clip.clipId,
                                  "move",
                                  clip.from,
                                  clip.to,
                                )
                              }
                              onClick={(event) => {
                                event.stopPropagation();
                                setSelection({ track: track.key, clipId: clip.clipId });
                              }}
                            >
                              <div
                                style={{
                                  position: "absolute",
                                  inset: 0,
                                  background:
                                    "linear-gradient(180deg, rgba(255,255,255,0.26) 0%, rgba(0,0,0,0.08) 100%)",
                                }}
                              />
                              <div
                                style={{
                                  position: "relative",
                                  display: "grid",
                                  height: "100%",
                                  padding: "12px 16px",
                                  boxSizing: "border-box",
                                }}
                              >
                                <div
                                  style={{
                                    fontSize: 14,
                                    fontWeight: 800,
                                    color: "#101010",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                    whiteSpace: "nowrap",
                                  }}
                                >
                                  {label}
                                </div>
                                <div
                                  style={{
                                    alignSelf: "end",
                                    fontSize: 12,
                                    color: "rgba(16,16,16,0.78)",
                                    fontFamily: MONO_FONT,
                                  }}
                                >
                                  {clip.from} - {clip.to}
                                </div>
                              </div>

                              <div
                                style={{
                                  position: "absolute",
                                  left: 0,
                                  top: 0,
                                  bottom: 0,
                                  width: 10,
                                  cursor: "ew-resize",
                                  background: "rgba(0,0,0,0.18)",
                                }}
                                onPointerDown={(event) =>
                                  startDrag(
                                    event,
                                    track.key,
                                    clip.clipId,
                                    "resize-start",
                                    clip.from,
                                    clip.to,
                                  )
                                }
                              />
                              <div
                                style={{
                                  position: "absolute",
                                  right: 0,
                                  top: 0,
                                  bottom: 0,
                                  width: 10,
                                  cursor: "ew-resize",
                                  background: "rgba(0,0,0,0.18)",
                                }}
                                onPointerDown={(event) =>
                                  startDrag(
                                    event,
                                    track.key,
                                    clip.clipId,
                                    "resize-end",
                                    clip.from,
                                    clip.to,
                                  )
                                }
                              />
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}

                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    bottom: 0,
                    left: TRACK_HEADER_WIDTH + currentFrame * pxPerFrame,
                    width: 2,
                    background: "#ffe082",
                    boxShadow: "0 0 0 1px rgba(0,0,0,0.35)",
                    pointerEvents: "none",
                    zIndex: 5,
                  }}
                />
              </div>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                gap: 10,
              }}
            >
              <MetaPill label="Duration" value={`${preset.durationInFrames}f`} />
              <MetaPill label="FPS" value={`${preset.fps}`} />
              <MetaPill label="Playhead" value={formatTime(currentFrame, preset.fps)} />
            </div>
          </div>

          <div
            style={{
              ...panelStyle,
              padding: 18,
              display: "grid",
              gridTemplateRows: "auto 1fr",
              gap: 14,
              minHeight: 0,
            }}
          >
            <div style={{ display: "grid", gap: 4 }}>
              <div
                style={{
                  fontSize: 12,
                  letterSpacing: "0.14em",
                  textTransform: "uppercase",
                  color: "#97886c",
                }}
              >
                Inspector
              </div>
              <div style={{ fontSize: 24, fontWeight: 800 }}>
                {selectedClip
                  ? selection?.track === "scenes"
                    ? getSceneLabel(selectedClip as SceneClip)
                    : getSubtitleLabel(selectedClip as SubtitleClip)
                  : "クリップ未選択"}
              </div>
            </div>

            <div
              style={{
                overflowY: "auto",
                paddingRight: 6,
                display: "grid",
                alignContent: "start",
                gap: 14,
              }}
            >
              {!selectedClip && (
                <div
                  style={{
                    borderRadius: 18,
                    padding: 16,
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: "#bab4a5",
                    lineHeight: 1.6,
                    fontSize: 15,
                  }}
                >
                  タイムライン上のクリップを選ぶと、ここで数値やテキストを直接編集できます。
                </div>
              )}

              {currentScene && (
                <>
                  <LabeledField label="ラベル">
                    <input
                      value={currentScene.label ?? ""}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          label: event.target.value || undefined,
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="開始フレーム">
                    <input
                      type="number"
                      value={currentScene.from}
                      min={0}
                      max={currentScene.to - 1}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          from: clamp(
                            Number(event.target.value),
                            0,
                            currentScene.to - 1,
                          ),
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="終了フレーム">
                    <input
                      type="number"
                      value={currentScene.to}
                      min={currentScene.from + 1}
                      max={preset.durationInFrames}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          to: clamp(
                            Number(event.target.value),
                            currentScene.from + 1,
                            preset.durationInFrames,
                          ),
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="画像パス" mono>
                    <input
                      value={currentScene.src}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          src: event.target.value,
                        }))
                      }
                      style={{ ...inputStyle, fontFamily: MONO_FONT, fontSize: 13 }}
                    />
                  </LabeledField>

                  <LabeledField label="モーション">
                    <select
                      value={currentScene.motionType}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          motionType: event.target.value as SceneClip["motionType"],
                        }))
                      }
                      style={inputStyle}
                    >
                      <option value="zoom_in">zoom_in</option>
                      <option value="zoom_out">zoom_out</option>
                      <option value="pan_right">pan_right</option>
                      <option value="pan_left">pan_left</option>
                      <option value="tilt_up">tilt_up</option>
                      <option value="tilt_down">tilt_down</option>
                      <option value="shake">shake</option>
                      <option value="static">static</option>
                    </select>
                  </LabeledField>

                  <LabeledField label="モーションプロファイル">
                    <select
                      value={currentScene.motionProfile}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          motionProfile: event.target.value as SceneClip["motionProfile"],
                        }))
                      }
                      style={inputStyle}
                    >
                      <option value="standard">standard</option>
                      <option value="gentle">gentle</option>
                      <option value="still">still</option>
                    </select>
                  </LabeledField>

                  <LabeledField label="ベース拡大率">
                    <input
                      type="number"
                      step={0.01}
                      value={currentScene.baseScale}
                      min={0.5}
                      max={2}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          baseScale: clamp(Number(event.target.value), 0.5, 2),
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="Crop X (%)">
                    <input
                      type="number"
                      step={1}
                      value={currentScene.cropXPercent}
                      min={-50}
                      max={50}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          cropXPercent: clamp(Number(event.target.value), -50, 50),
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="Crop Y (%)">
                    <input
                      type="number"
                      step={1}
                      value={currentScene.cropYPercent}
                      min={-50}
                      max={50}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SceneClip),
                          cropYPercent: clamp(Number(event.target.value), -50, 50),
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>
                </>
              )}

              {currentSubtitle && (
                <>
                  <LabeledField label="ラベル">
                    <input
                      value={currentSubtitle.label ?? ""}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          label: event.target.value || undefined,
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="開始フレーム">
                    <input
                      type="number"
                      value={currentSubtitle.from}
                      min={0}
                      max={currentSubtitle.to - 1}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          from: clamp(
                            Number(event.target.value),
                            0,
                            currentSubtitle.to - 1,
                          ),
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="終了フレーム">
                    <input
                      type="number"
                      value={currentSubtitle.to}
                      min={currentSubtitle.from + 1}
                      max={preset.durationInFrames}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          to: clamp(
                            Number(event.target.value),
                            currentSubtitle.from + 1,
                            preset.durationInFrames,
                          ),
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="字幕テキスト">
                    <textarea
                      value={currentSubtitle.text}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          text: event.target.value,
                        }))
                      }
                      rows={6}
                      style={{ ...inputStyle, resize: "vertical", lineHeight: 1.45 }}
                    />
                  </LabeledField>

                  <LabeledField label="フォントサイズ">
                    <input
                      type="number"
                      value={currentSubtitle.fontSize ?? ""}
                      min={24}
                      max={240}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          fontSize: event.target.value
                            ? clamp(Number(event.target.value), 24, 240)
                            : undefined,
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="X (%)">
                    <input
                      type="number"
                      value={currentSubtitle.xPercent ?? ""}
                      min={0}
                      max={100}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          xPercent: event.target.value
                            ? clamp(Number(event.target.value), 0, 100)
                            : undefined,
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="Y (%)">
                    <input
                      type="number"
                      value={currentSubtitle.yPercent ?? ""}
                      min={0}
                      max={100}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          yPercent: event.target.value
                            ? clamp(Number(event.target.value), 0, 100)
                            : undefined,
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="Max Width (%)">
                    <input
                      type="number"
                      value={currentSubtitle.maxWidthPercent ?? ""}
                      min={20}
                      max={100}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          maxWidthPercent: event.target.value
                            ? clamp(Number(event.target.value), 20, 100)
                            : undefined,
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>

                  <LabeledField label="行間(px)">
                    <input
                      type="number"
                      value={currentSubtitle.lineGap ?? ""}
                      min={0}
                      max={40}
                      onChange={(event) =>
                        updateSelection((clip) => ({
                          ...(clip as SubtitleClip),
                          lineGap: event.target.value
                            ? clamp(Number(event.target.value), 0, 40)
                            : undefined,
                        }))
                      }
                      style={inputStyle}
                    />
                  </LabeledField>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
