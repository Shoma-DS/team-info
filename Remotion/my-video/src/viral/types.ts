// ─── analysis.json の型定義 ────────────────────────────────────────────────

export type Platform = "tiktok" | "shorts" | "reels";

export interface CutSegment {
  start: number;       // 秒
  end: number;         // 秒
  start_frame: number;
  end_frame: number;
}

export interface FaceDetection {
  frame: number;
  time: number;
  x: number;          // 0-1 (相対座標)
  y: number;
  size: number;
  confidence: number;
}

export interface TextRegion {
  frame: number;
  time: number;
  x: number;
  y: number;
  text: string;
  confidence: number;
}

export interface CameraMotion {
  type: "zoom" | "pan_left" | "pan_right" | "tilt_up" | "tilt_down" | "shake" | "static";
  start: number;       // 秒
  end: number;
}

export interface VideoStructure {
  cuts: CutSegment[];
  faces: FaceDetection[];
  text_regions: TextRegion[];
  camera_motion: CameraMotion[];
  important_frames: number[];
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  words?: { word: string; start: number; end: number }[];
}

export interface SpeechStructure {
  transcript: TranscriptSegment[];
  full_text: string;
  words_per_minute: number;
  keywords: string[];
  emotional_intensity: "low" | "medium" | "high";
  pauses: { start: number; end: number; duration: number }[];
}

export interface ViralStructure {
  hook_time: number;
  hook_type: "question" | "statement" | "visual" | "unknown";
  pattern_interrupts: number[];
  loop_point: number | null;
  information_density: "low" | "medium" | "high";
  tone: "educational" | "entertainment" | "curiosity" | "general";
}

export interface AnalysisJson {
  duration: number;
  fps: number;
  platform: Platform;
  resolution: { width: number; height: number };
  video_structure: VideoStructure;
  speech_structure: SpeechStructure;
  viral_structure: ViralStructure;
}

// ─── Remotion コンポーネント Props ─────────────────────────────────────────

export interface PlatformConfig {
  width: number;
  height: number;
  maxDuration: number;
  subtitleFontSize: number;
  subtitleY: number;      // 画面下からの % (0-100)
}

export const PLATFORM_CONFIG: Record<Platform, PlatformConfig> = {
  tiktok:  { width: 1080, height: 1920, maxDuration: 60,  subtitleFontSize: 52, subtitleY: 75 },
  shorts:  { width: 1080, height: 1920, maxDuration: 60,  subtitleFontSize: 48, subtitleY: 72 },
  reels:   { width: 1080, height: 1920, maxDuration: 90,  subtitleFontSize: 44, subtitleY: 70 },
};
