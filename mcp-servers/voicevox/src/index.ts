#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { execSync } from "child_process";
import { fileURLToPath } from "url";

const VOICEVOX_API = "http://127.0.0.1:50021";

// プロジェクトルートを算出（mcp-servers/voicevox/dist/index.js から3階層上）
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROJECT_ROOT = join(__dirname, "..", "..", "..");
const CONFIG_FILE = join(PROJECT_ROOT, "Remotion", "configs", "voice_config.json");
const SCRIPT_DIR = join(PROJECT_ROOT, "Remotion", "scripts", "voice_scripts");
const OUTPUT_DIR = join(PROJECT_ROOT, "Remotion", "output", "audio");
const GENERATE_SCRIPT = join(PROJECT_ROOT, "Remotion", "generate_voice.py");
const VENV_PYTHON = join(PROJECT_ROOT, "Remotion", ".venv", "bin", "python");

async function voicevoxFetch(path: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(`${VOICEVOX_API}${path}`, options);
  if (!res.ok) {
    throw new Error(`VOICEVOX API error: ${res.status} ${res.statusText}`);
  }
  return res;
}

// ---- MCP Server ----

const server = new McpServer({
  name: "voicevox",
  version: "1.0.0",
});

// Tool 1: スピーカー一覧取得
server.tool(
  "voicevox_get_speakers",
  "VOICEVOXエンジンから利用可能なスピーカーとスタイルの一覧を取得する",
  {},
  async () => {
    try {
      const res = await voicevoxFetch("/speakers");
      const speakers = (await res.json()) as Array<{
        name: string;
        styles: Array<{ name: string; id: number }>;
      }>;

      const lines: string[] = [];
      for (const speaker of speakers) {
        for (const style of speaker.styles) {
          lines.push(`${speaker.name} / ${style.name} (id: ${style.id})`);
        }
      }

      return {
        content: [{ type: "text" as const, text: lines.join("\n") }],
      };
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      return {
        content: [{ type: "text" as const, text: `エラー: ${msg}\nVOICEVOXエンジンが http://127.0.0.1:50021 で起動しているか確認してください。` }],
        isError: true,
      };
    }
  }
);

// Tool 2: プリセット一覧取得
server.tool(
  "voicevox_get_presets",
  "VOICEVOXエンジンのプリセット一覧を取得する",
  {},
  async () => {
    try {
      const res = await voicevoxFetch("/presets");
      const presets = (await res.json()) as Array<{
        id: number;
        name: string;
        speaker_uuid: string;
        style_id: number;
        speedScale: number;
        pitchScale: number;
        volumeScale: number;
      }>;

      const lines = presets.map(
        (p) => `id:${p.id} "${p.name}" (style_id:${p.style_id}, speed:${p.speedScale}, pitch:${p.pitchScale}, volume:${p.volumeScale})`
      );

      return {
        content: [{ type: "text" as const, text: lines.length > 0 ? lines.join("\n") : "プリセットはありません" }],
      };
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      return {
        content: [{ type: "text" as const, text: `エラー: ${msg}` }],
        isError: true,
      };
    }
  }
);

// Tool 3: プロファイル一覧取得（voice_config.json）
server.tool(
  "voicevox_get_profiles",
  "voice_config.json に定義された音声設定プロファイル一覧を取得する",
  {},
  async () => {
    try {
      const raw = readFileSync(CONFIG_FILE, "utf-8");
      const configs = JSON.parse(raw) as Record<string, Record<string, unknown>>;

      const lines: string[] = [];
      let i = 1;
      for (const [name, profile] of Object.entries(configs)) {
        const speaker = profile.speaker_name ?? "(preset)";
        const style = profile.style_name ?? "";
        const speed = profile.speed ?? 1.0;
        lines.push(`${i}. ${name}: ${speaker} / ${style} (speed: ${speed})`);
        i++;
      }

      return {
        content: [{ type: "text" as const, text: lines.join("\n") }],
      };
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      return {
        content: [{ type: "text" as const, text: `エラー: ${msg}` }],
        isError: true,
      };
    }
  }
);

// Tool 4: テスト音声生成（短いテキスト1文）
server.tool(
  "voicevox_test_speech",
  "短いテキストを音声化してWAVファイルに保存する（試し聞き用）。テキストは200文字以内。",
  {
    text: z.string().max(200).describe("音声化するテキスト（200文字以内）"),
    speaker_id: z.number().optional().describe("スピーカーID（省略時はデフォルトプロファイルを使用）"),
    profile_name: z.string().optional().describe("voice_config.jsonのプロファイル名（speaker_idより優先）"),
    speed: z.number().optional().describe("話速（デフォルト: プロファイルの値）"),
  },
  async ({ text, speaker_id, profile_name, speed }) => {
    try {
      let speakerId = speaker_id ?? 0;
      let effectiveSpeed = speed;

      // プロファイル名が指定されている場合
      if (profile_name) {
        const raw = readFileSync(CONFIG_FILE, "utf-8");
        const configs = JSON.parse(raw) as Record<string, Record<string, unknown>>;
        const profile = configs[profile_name];
        if (!profile) {
          return {
            content: [{ type: "text" as const, text: `エラー: プロファイル '${profile_name}' が見つかりません` }],
            isError: true,
          };
        }

        // speaker_idをスピーカー名+スタイル名から解決
        const speakerName = profile.speaker_name as string | undefined;
        const styleName = profile.style_name as string | undefined;

        if (speakerName && styleName) {
          const res = await voicevoxFetch("/speakers");
          const speakers = (await res.json()) as Array<{
            name: string;
            styles: Array<{ name: string; id: number }>;
          }>;
          for (const s of speakers) {
            if (s.name === speakerName) {
              for (const st of s.styles) {
                if (st.name === styleName) {
                  speakerId = st.id;
                }
              }
            }
          }
        }

        if (effectiveSpeed === undefined) {
          effectiveSpeed = profile.speed as number | undefined;
        }
      }

      // audio_query生成
      const queryRes = await voicevoxFetch(
        `/audio_query?text=${encodeURIComponent(text)}&speaker=${speakerId}`,
        { method: "POST" }
      );
      const query = (await queryRes.json()) as Record<string, unknown>;

      if (effectiveSpeed !== undefined) {
        query.speedScale = effectiveSpeed;
      }

      // 音声合成
      const synthRes = await voicevoxFetch(
        `/synthesis?speaker=${speakerId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(query),
        }
      );
      const wavBuffer = Buffer.from(await synthRes.arrayBuffer());

      // ファイルに保存
      mkdirSync(OUTPUT_DIR, { recursive: true });
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
      const outputPath = join(OUTPUT_DIR, `test_${timestamp}.wav`);
      writeFileSync(outputPath, wavBuffer);

      return {
        content: [{ type: "text" as const, text: `テスト音声を生成しました: ${outputPath}\nスピーカーID: ${speakerId}, テキスト: "${text}"` }],
      };
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      return {
        content: [{ type: "text" as const, text: `エラー: ${msg}` }],
        isError: true,
      };
    }
  }
);

// Tool 5: 一括音声生成（既存Pythonスクリプトを呼び出し）
server.tool(
  "voicevox_generate_full",
  "台本ファイルを指定して一括音声生成する。並列処理で高速。既存のgenerate_voice.pyを内部で実行する。",
  {
    script_name: z.string().describe("台本ファイル名（voice_scripts/内のファイル名、例: '北欧神話_氷と炎の世界の始まり_20260211.md'）"),
    profile_name: z.string().describe("voice_config.jsonのプロファイル名（例: 'shikoku_metan_whisper'）"),
    theme: z.string().describe("出力ファイルのテーマ名（例: '北欧神話_氷と炎の世界の始まり'）"),
  },
  async ({ script_name, profile_name, theme }) => {
    try {
      const cmd = `cd "${join(PROJECT_ROOT, "Remotion")}" && "${VENV_PYTHON}" generate_voice.py --script "${script_name}" --profile "${profile_name}" --theme "${theme}"`;

      const output = execSync(cmd, {
        encoding: "utf-8",
        timeout: 600000, // 10分タイムアウト
        maxBuffer: 10 * 1024 * 1024,
      });

      return {
        content: [{ type: "text" as const, text: output }],
      };
    } catch (e: unknown) {
      const msg = e instanceof Error ? (e as Error & { stderr?: string }).stderr || e.message : String(e);
      return {
        content: [{ type: "text" as const, text: `音声生成エラー:\n${msg}` }],
        isError: true,
      };
    }
  }
);

// ---- Start ----

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((e) => {
  console.error("MCP Server error:", e);
  process.exit(1);
});
