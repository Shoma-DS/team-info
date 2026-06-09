/**
 * Builds cutcli draft inputs from a CapCut package exported by Remotion.
 * It can write JSON payloads and, when cutcli is installed, run the commands
 * that create a CapCut/Jianying draft with images, audio, and captions.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const defaultPackageRoot = path.resolve(projectRoot, "..", "..", "outputs", "capcut");
const args = parseArgs(process.argv.slice(2));

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});

async function main() {
  const canRunCutcli = args.runIfAvailable ? await isCommandAvailable(args.cutcli) : args.run;
  if (args.runIfAvailable && !canRunCutcli) {
    console.warn(`cutcli executable not found: ${args.cutcli}`);
    console.warn("Prepared draft payloads will be written, but CapCut draft creation will be skipped.");
  }

  const packages = await resolvePackages(args);
  if (packages.length === 0) {
    throw new Error("No CapCut packages found. Run export:capcut first.");
  }

  const results = [];
  for (const packageDir of packages) {
    const result = await preparePackage(packageDir);
    results.push(result);
    if (canRunCutcli) {
      result.runResult = await runCutcli(result);
    }
  }

  console.log("cutcli draft generation prepared:");
  for (const result of results) {
    const runStatus = result.runResult ? ` draftId=${result.runResult.draftId ?? "unknown"}` : "";
    console.log(`- ${result.name}: ${result.cutcliDir}${runStatus}`);
  }
}

function parseArgs(argv) {
  const parsed = {
    packageDirs: [],
    all: false,
    run: false,
    runIfAvailable: false,
    mediaUrlMode: "path",
    cutcli: "cutcli",
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--package") {
      const value = argv[++i];
      if (!value) throw new Error("--package requires a directory path.");
      parsed.packageDirs.push(path.resolve(process.cwd(), value));
    } else if (arg === "--all") {
      parsed.all = true;
    } else if (arg === "--run") {
      parsed.run = true;
    } else if (arg === "--run-if-available") {
      parsed.runIfAvailable = true;
    } else if (arg === "--media-url-mode") {
      const value = argv[++i];
      if (!["file-url", "path"].includes(value)) {
        throw new Error("--media-url-mode must be file-url or path.");
      }
      parsed.mediaUrlMode = value;
    } else if (arg === "--cutcli") {
      const value = argv[++i];
      if (!value) throw new Error("--cutcli requires an executable path.");
      parsed.cutcli = value;
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return parsed;
}

function printHelp() {
  console.log(`Usage:
  npm run create:capcut-draft -- --package "../../outputs/capcut/TenshokuShort20260602"
  npm run create:capcut-draft -- --all
  npm run create:capcut-draft -- --all --run
  npm run create:capcut-draft -- --all --run-if-available

Options:
  --package <dir>             CapCut package directory. Can be repeated.
  --all                       Use every package under ../../outputs/capcut.
  --run                       Run cutcli after writing JSON payloads.
  --run-if-available          Run cutcli only when it is available on this PC.
  --cutcli <path>             cutcli executable. Defaults to cutcli.
  --media-url-mode <mode>     file-url or path. Defaults to file-url.
`);
}

function isCommandAvailable(command) {
  return new Promise((resolve) => {
    const probe = process.platform === "win32" ? "where" : "command";
    const probeArgs = process.platform === "win32" ? [command] : ["-v", command];
    const child = spawn(probe, probeArgs, { shell: process.platform !== "win32" });
    child.on("error", () => resolve(false));
    child.on("close", (code) => resolve(code === 0));
  });
}

async function resolvePackages(parsedArgs) {
  const packageSet = new Set(parsedArgs.packageDirs);
  if (parsedArgs.all) {
    const entries = await fs.readdir(defaultPackageRoot, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const packageDir = path.join(defaultPackageRoot, entry.name);
      try {
        await fs.access(path.join(packageDir, "timeline.json"));
        packageSet.add(packageDir);
      } catch {
        // Skip incomplete package folders.
      }
    }
  }
  return [...packageSet].sort();
}

async function preparePackage(packageDir) {
  const timelinePath = path.join(packageDir, "timeline.json");
  const timeline = JSON.parse(await fs.readFile(timelinePath, "utf8"));
  const cutcliDir = path.join(packageDir, "cutcli");
  await fs.mkdir(cutcliDir, { recursive: true });

  const images = buildImageInfos(timeline, packageDir);
  const audios = buildAudioInfos(timeline, packageDir);
  const captions = buildCaptions(timeline);
  const summary = {
    name: timeline.name,
    width: timeline.width,
    height: timeline.height,
    duration: secondsToMicros(timeline.durationSeconds),
    images: images.length,
    audios: audios.length,
    captions: captions.length,
    mediaUrlMode: args.mediaUrlMode,
  };

  await writeJson(path.join(cutcliDir, "images.json"), images);
  await writeJson(path.join(cutcliDir, "audios.json"), audios);
  await writeJson(path.join(cutcliDir, "captions.json"), captions);
  await writeJson(path.join(cutcliDir, "summary.json"), summary);
  await fs.writeFile(path.join(cutcliDir, "create_draft.ps1"), buildPowershellRunner(timeline, cutcliDir), "utf8");
  await fs.writeFile(path.join(cutcliDir, "create_draft.sh"), buildShellRunner(timeline, cutcliDir), "utf8");

  return {
    name: timeline.name,
    packageDir,
    cutcliDir,
    width: timeline.width,
    height: timeline.height,
    imagesPath: path.join(cutcliDir, "images.json"),
    audiosPath: path.join(cutcliDir, "audios.json"),
    captionsPath: path.join(cutcliDir, "captions.json"),
    counts: summary,
  };
}

function buildImageInfos(timeline, packageDir) {
  const imageSegments = [];
  for (const scene of timeline.tracks.scenes ?? []) {
    if (scene.type === "section" && Array.isArray(scene.visuals) && scene.visuals.length > 0) {
      const sorted = scene.visuals
        .filter((visual) => visual.source?.packagePath)
        .sort((a, b) => a.startFrame - b.startFrame);
      for (let index = 0; index < sorted.length; index += 1) {
        const visual = sorted[index];
        const next = sorted[index + 1];
        const start = visual.start ?? scene.start;
        const end = next?.start ?? scene.end;
        imageSegments.push(imageInfo(visual.source, start, end, timeline, packageDir));
      }
      continue;
    }

    const visual = scene.visual ?? scene.photo ?? scene.image ?? scene.image1;
    if (visual?.packagePath) {
      imageSegments.push(imageInfo(visual, scene.start, scene.end, timeline, packageDir));
    }
  }

  return imageSegments.filter(Boolean);
}

function imageInfo(asset, start, end, timeline, packageDir) {
  const media = mediaUrl(asset, packageDir);
  if (!media) return null;
  return {
    imageUrl: media,
    width: timeline.width,
    height: timeline.height,
    start: secondsToMicros(start),
    end: secondsToMicros(end),
    inAnimationDuration: 120000,
    outAnimationDuration: 120000,
  };
}

function buildAudioInfos(timeline, packageDir) {
  const audioInfos = [];
  if (timeline.tracks.audio?.source?.packagePath) {
    const audio = timeline.tracks.audio;
    audioInfos.push({
      audioUrl: mediaUrl(audio.source, packageDir),
      duration: secondsToMicros(audio.end - audio.start),
      start: secondsToMicros(audio.start),
      end: secondsToMicros(audio.end),
      volume: audio.volume ?? 1,
    });
  }

  for (const cue of timeline.tracks.sfx ?? []) {
    if (!cue.source?.packagePath) continue;
    const start = cue.start ?? 0;
    const duration = framesToMicros(cue.durationFrames, timeline.fps);
    audioInfos.push({
      audioUrl: mediaUrl(cue.source, packageDir),
      duration,
      start: secondsToMicros(start),
      end: secondsToMicros(start) + duration,
      volume: cue.volume ?? 0.32,
    });
  }

  return audioInfos.filter((item) => item.audioUrl);
}

function buildCaptions(timeline) {
  const fontSize = timeline.height > timeline.width ? 8 : 7;
  return (timeline.tracks.subtitles ?? []).map((entry) => ({
    text: entry.text,
    start: secondsToMicros(entry.start),
    end: secondsToMicros(entry.end),
    fontSize,
  }));
}

function mediaUrl(asset, packageDir) {
  if (!asset?.packagePath || asset.exists === false) return null;
  const fullPath = path.resolve(packageDir, asset.packagePath);
  return args.mediaUrlMode === "path" ? fullPath : pathToFileURL(fullPath).href;
}

function secondsToMicros(seconds) {
  return Math.max(0, Math.round(Number(seconds) * 1000000));
}

function framesToMicros(frames, fps) {
  return Math.max(0, Math.round((Number(frames) / Number(fps || 30)) * 1000000));
}

async function writeJson(filePath, value) {
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function buildPowershellRunner(timeline, cutcliDir) {
  const draftCreate = `cutcli draft create --width ${timeline.width} --height ${timeline.height}`;
  return `# This file creates a CapCut draft from the exported Remotion package.
# Run it after installing cutcli and confirming CapCut's draft path.
$ErrorActionPreference = "Stop"
$cutcliDir = "${escapePs(cutcliDir)}"
$draftJson = & ${draftCreate}
$draft = $draftJson | ConvertFrom-Json
$draftId = $draft.draftId
Write-Host "Created draft: $draftId"
& cutcli images add $draftId --image-infos "@$cutcliDir\\images.json"
& cutcli audios add $draftId --audio-infos "@$cutcliDir\\audios.json"
& cutcli captions add $draftId --captions "@$cutcliDir\\captions.json" --font "Yu Gothic UI" --font-size ${timeline.height > timeline.width ? 10 : 8} --bold --text-color "#FFFFFF" --border-color "#000000" --border-width 5 --alignment 0 --transform-x 0 --transform-y -0.72 --line-spacing 0.85
Write-Host "CapCut draft ready: $draftId"
`;
}

function buildShellRunner(timeline, cutcliDir) {
  return `#!/usr/bin/env bash
# This file creates a CapCut draft from the exported Remotion package.
set -euo pipefail
CUTCLI_DIR="${cutcliDir.replaceAll("\\", "/")}"
DRAFT_JSON="$(cutcli draft create --width ${timeline.width} --height ${timeline.height})"
DRAFT_ID="$(node -e 'let s="";process.stdin.on("data",d=>s+=d);process.stdin.on("end",()=>console.log(JSON.parse(s).draftId))' <<< "$DRAFT_JSON")"
echo "Created draft: $DRAFT_ID"
cutcli images add "$DRAFT_ID" --image-infos "@$CUTCLI_DIR/images.json"
cutcli audios add "$DRAFT_ID" --audio-infos "@$CUTCLI_DIR/audios.json"
cutcli captions add "$DRAFT_ID" --captions "@$CUTCLI_DIR/captions.json" --font "Yu Gothic UI" --font-size ${timeline.height > timeline.width ? 10 : 8} --bold --text-color "#FFFFFF" --border-color "#000000" --border-width 5 --alignment 0 --transform-x 0 --transform-y -0.72 --line-spacing 0.85
echo "CapCut draft ready: $DRAFT_ID"
`;
}

function escapePs(value) {
  return value.replaceAll("`", "``").replaceAll('"', '`"');
}

async function runCutcli(prepared) {
  const draft = await runCommand(args.cutcli, ["draft", "create", "--width", String(prepared.width), "--height", String(prepared.height)]);
  const draftId = parseDraftId(draft.stdout);
  if (!draftId) {
    throw new Error(`cutcli draft create did not return draftId. Output: ${draft.stdout}`);
  }

  await runCommand(args.cutcli, ["images", "add", draftId, "--image-infos", `@${prepared.imagesPath}`]);
  await runCommand(args.cutcli, ["audios", "add", draftId, "--audio-infos", `@${prepared.audiosPath}`]);
  await runCommand(args.cutcli, [
    "captions",
    "add",
    draftId,
    "--captions",
    `@${prepared.captionsPath}`,
    "--font-size",
    prepared.height > prepared.width ? "10" : "8",
    "--bold",
    "--text-color",
    "#FFFFFF",
    "--border-color",
    "#000000",
    "--border-width",
    "5",
    "--alignment",
    "0",
    "--transform-x",
    "0",
    "--transform-y",
    "-0.72",
    "--line-spacing",
    "0.85",
  ]);

  return { draftId };
}

function runCommand(command, commandArgs) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, commandArgs, { shell: process.platform === "win32" });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
      process.stdout.write(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
      process.stderr.write(chunk);
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(`${command} ${commandArgs.join(" ")} failed with code ${code}\n${stderr}`));
      }
    });
  });
}

function parseDraftId(output) {
  const trimmed = output.trim();
  const jsonStart = trimmed.lastIndexOf("{");
  if (jsonStart < 0) return null;
  try {
    const parsed = JSON.parse(trimmed.slice(jsonStart));
    return parsed.draftId ?? null;
  } catch {
    return null;
  }
}
