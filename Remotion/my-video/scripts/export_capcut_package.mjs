/**
 * Exports Remotion ViralTemplate compositions into CapCut-ready packages.
 * It reads TSX props, copies media assets, writes an SRT caption file,
 * and emits timeline metadata for manual import or draft-tool automation.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import ts from "typescript";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const publicRoot = path.join(projectRoot, "public");
const srcRoot = path.join(projectRoot, "src");
const defaultOutputRoot = path.resolve(projectRoot, "..", "..", "outputs", "capcut");

const args = parseArgs(process.argv.slice(2));

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});

async function main() {
  const sources = await resolveSources(args);
  if (sources.length === 0) {
    throw new Error("No ViralTemplate sources found. Pass --source <file> or --all.");
  }

  const exported = [];
  for (const sourceFile of sources) {
    const packages = await exportSource(sourceFile);
    exported.push(...packages);
  }

  if (exported.length === 0) {
    throw new Error("No ViralTemplate JSX instances were exported.");
  }

  console.log("CapCut package export complete:");
  for (const item of exported) {
    console.log(`- ${item.name}: ${item.outputDir}`);
  }
}

function parseArgs(argv) {
  const parsed = {
    all: false,
    source: [],
    outDir: defaultOutputRoot,
    includeMissing: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--all") {
      parsed.all = true;
    } else if (arg === "--source") {
      const value = argv[++i];
      if (!value) throw new Error("--source requires a file path.");
      parsed.source.push(path.resolve(process.cwd(), value));
    } else if (arg === "--out-dir") {
      const value = argv[++i];
      if (!value) throw new Error("--out-dir requires a directory path.");
      parsed.outDir = path.resolve(process.cwd(), value);
    } else if (arg === "--include-missing") {
      parsed.includeMissing = true;
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
  npm run export:capcut -- --source "src/viral/TenshokuShort20260602.tsx"
  npm run export:capcut -- --all

Options:
  --source <file>       Export one TSX file. Can be repeated.
  --all                 Scan src/viral recursively for ViralTemplate usage.
  --out-dir <dir>       Output directory. Defaults to ../../outputs/capcut.
  --include-missing     Keep missing assets in timeline instead of failing copy.
`);
}

async function resolveSources(parsedArgs) {
  const sourceSet = new Set(parsedArgs.source);

  if (parsedArgs.all) {
    const files = await walk(srcRoot);
    for (const file of files) {
      if (!file.endsWith(".tsx")) continue;
      const content = await fs.readFile(file, "utf8");
      if (content.includes("<ViralTemplate")) {
        sourceSet.add(file);
      }
    }
  }

  return [...sourceSet].sort();
}

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walk(fullPath)));
    } else {
      files.push(fullPath);
    }
  }
  return files;
}

async function exportSource(sourcePath) {
  const sourceText = await fs.readFile(sourcePath, "utf8");
  const source = ts.createSourceFile(sourcePath, sourceText, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const env = await buildEnvironment(source, sourcePath);
  const viralTemplates = collectViralTemplates(source, env);

  const exported = [];
  for (let index = 0; index < viralTemplates.length; index += 1) {
    const props = viralTemplates[index];
    const name = pickPackageName(sourcePath, props, index);
    const outputDir = path.join(args.outDir, name);
    await writePackage({ sourcePath, props, name, outputDir });
    exported.push({ name, outputDir });
  }

  return exported;
}

function collectViralTemplates(source, env) {
  const templates = [];

  const traverse = (node, scope) => {
    let nextScope = scope;
    if (isFunctionWithBody(node)) {
      nextScope = buildLocalEnvironment(node.body, source, scope);
    }

    if (ts.isJsxSelfClosingElement(node) && node.tagName.getText(source) === "ViralTemplate") {
      templates.push(evaluateJsxProps(node, source, nextScope));
      return;
    }

    ts.forEachChild(node, (child) => traverse(child, nextScope));
  };

  traverse(source, env);
  return templates;
}

function isFunctionWithBody(node) {
  return (
    (ts.isFunctionDeclaration(node) ||
      ts.isFunctionExpression(node) ||
      ts.isArrowFunction(node) ||
      ts.isMethodDeclaration(node)) &&
    node.body &&
    ts.isBlock(node.body)
  );
}

function buildLocalEnvironment(body, source, parentEnv) {
  const localEnv = new Map(parentEnv);
  for (const statement of body.statements) {
    if (!ts.isVariableStatement(statement)) continue;
    for (const decl of statement.declarationList.declarations) {
      if (!ts.isIdentifier(decl.name) || !decl.initializer) continue;
      const name = decl.name.text;
      if (ts.isArrowFunction(decl.initializer)) {
        localEnv.set(name, { type: "function", node: decl.initializer });
      } else {
        try {
          localEnv.set(name, evaluateExpression(decl.initializer, source, localEnv));
        } catch {
          // Some helper components contain runtime-only locals that are not
          // needed for the ViralTemplate export contract.
        }
      }
    }
  }
  return localEnv;
}

async function buildEnvironment(source, sourcePath) {
  const env = new Map();
  const sourceDir = path.dirname(sourcePath);

  for (const statement of source.statements) {
    if (ts.isImportDeclaration(statement)) {
      await loadSubtitleImport(statement, source, sourceDir, env);
    }
  }

  for (const statement of source.statements) {
    if (!ts.isVariableStatement(statement)) continue;
    for (const decl of statement.declarationList.declarations) {
      if (!ts.isIdentifier(decl.name) || !decl.initializer) continue;
      const name = decl.name.text;
      if (ts.isArrowFunction(decl.initializer)) {
        env.set(name, { type: "function", node: decl.initializer });
      } else {
        env.set(name, evaluateExpression(decl.initializer, source, env));
      }
    }
  }

  return env;
}

async function loadSubtitleImport(statement, source, sourceDir, env) {
  if (!statement.importClause?.namedBindings) return;
  if (!ts.isNamedImports(statement.importClause.namedBindings)) return;

  const names = statement.importClause.namedBindings.elements.map((element) => element.name.text);
  if (!names.includes("SUBTITLE_TIMELINE")) return;

  const specifier = statement.moduleSpecifier;
  if (!ts.isStringLiteral(specifier)) return;

  const subtitlePath = await resolveTsModule(sourceDir, specifier.text);
  if (!subtitlePath) return;

  const subtitleText = await fs.readFile(subtitlePath, "utf8");
  const subtitleSource = ts.createSourceFile(subtitlePath, subtitleText, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);

  visit(subtitleSource, (node) => {
    if (!ts.isVariableStatement(node)) return;
    for (const decl of node.declarationList.declarations) {
      if (ts.isIdentifier(decl.name) && decl.name.text === "SUBTITLE_TIMELINE" && decl.initializer) {
        env.set("SUBTITLE_TIMELINE", evaluateExpression(decl.initializer, subtitleSource, env));
      }
    }
  });
}

async function resolveTsModule(baseDir, specifier) {
  const base = path.resolve(baseDir, specifier);
  const candidates = [base, `${base}.ts`, `${base}.tsx`, path.join(base, "index.ts"), path.join(base, "index.tsx")];
  for (const candidate of candidates) {
    try {
      const stat = await fs.stat(candidate);
      if (stat.isFile()) return candidate;
    } catch {
      // Try the next candidate.
    }
  }
  return null;
}

function evaluateJsxProps(node, source, env) {
  const props = {};
  for (const attr of node.attributes.properties) {
    if (!ts.isJsxAttribute(attr) || !attr.initializer) continue;
    const name = attr.name.text;
    if (ts.isStringLiteral(attr.initializer)) {
      props[name] = attr.initializer.text;
    } else if (ts.isJsxExpression(attr.initializer) && attr.initializer.expression) {
      props[name] = evaluateExpression(attr.initializer.expression, source, env);
    }
  }
  return props;
}

function evaluateExpression(node, source, env) {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  if (ts.isNumericLiteral(node)) return Number(node.text);
  if (node.kind === ts.SyntaxKind.TrueKeyword) return true;
  if (node.kind === ts.SyntaxKind.FalseKeyword) return false;
  if (ts.isIdentifier(node)) {
    if (env.has(node.text)) return env.get(node.text);
    return node.text;
  }
  if (ts.isTemplateExpression(node)) return evaluateTemplate(node, source, env);
  if (ts.isArrayLiteralExpression(node)) return node.elements.map((element) => evaluateExpression(element, source, env));
  if (ts.isObjectLiteralExpression(node)) return evaluateObject(node, source, env);
  if (ts.isCallExpression(node)) return evaluateCall(node, source, env);
  if (ts.isBinaryExpression(node)) return evaluateBinary(node, source, env);
  if (ts.isElementAccessExpression(node)) {
    const target = evaluateExpression(node.expression, source, env);
    const index = evaluateExpression(node.argumentExpression, source, env);
    return Array.isArray(target) ? target[index] : undefined;
  }
  if (ts.isParenthesizedExpression(node)) return evaluateExpression(node.expression, source, env);
  if (ts.isAsExpression(node) || ts.isTypeAssertionExpression(node) || ts.isNonNullExpression(node)) {
    return evaluateExpression(node.expression, source, env);
  }

  throw new Error(`Unsupported expression: ${node.getText(source).slice(0, 120)}`);
}

function evaluateTemplate(node, source, env) {
  let value = node.head.text;
  for (const span of node.templateSpans) {
    value += String(evaluateExpression(span.expression, source, env) ?? "");
    value += span.literal.text;
  }
  return value;
}

function evaluateObject(node, source, env) {
  const value = {};
  for (const prop of node.properties) {
    if (ts.isSpreadAssignment(prop)) {
      Object.assign(value, evaluateExpression(prop.expression, source, env));
      continue;
    }
    if (!ts.isPropertyAssignment(prop)) continue;
    const key = propertyNameToString(prop.name, source);
    value[key] = evaluateExpression(prop.initializer, source, env);
  }
  return value;
}

function propertyNameToString(name, source) {
  if (ts.isIdentifier(name) || ts.isStringLiteral(name) || ts.isNumericLiteral(name)) return name.text;
  return name.getText(source);
}

function evaluateCall(node, source, env) {
  const callName = node.expression.getText(source);
  const evaluatedArgs = node.arguments.map((arg) => evaluateExpression(arg, source, env));

  if (callName === "staticFile") {
    return evaluatedArgs[0];
  }

  if (callName === "Math.max") {
    return Math.max(...evaluatedArgs);
  }

  const fn = env.get(callName);
  if (fn?.type === "function") {
    return evaluateArrowFunction(fn.node, evaluatedArgs, source, env);
  }

  throw new Error(`Unsupported function call: ${node.getText(source).slice(0, 120)}`);
}

function evaluateArrowFunction(fn, args, source, outerEnv) {
  const localEnv = new Map(outerEnv);
  fn.parameters.forEach((param, index) => {
    if (ts.isIdentifier(param.name)) localEnv.set(param.name.text, args[index]);
  });

  if (ts.isBlock(fn.body)) {
    throw new Error(`Block arrow functions are not supported: ${fn.getText(source).slice(0, 120)}`);
  }

  return evaluateExpression(fn.body, source, localEnv);
}

function evaluateBinary(node, source, env) {
  const left = evaluateExpression(node.left, source, env);
  const right = evaluateExpression(node.right, source, env);

  switch (node.operatorToken.kind) {
    case ts.SyntaxKind.PlusToken:
      return typeof left === "string" || typeof right === "string" ? `${left}${right}` : left + right;
    case ts.SyntaxKind.MinusToken:
      return left - right;
    case ts.SyntaxKind.AsteriskToken:
      return left * right;
    case ts.SyntaxKind.SlashToken:
      return left / right;
    default:
      throw new Error(`Unsupported binary operator: ${node.operatorToken.getText(source)}`);
  }
}

function visit(node, callback) {
  callback(node);
  ts.forEachChild(node, (child) => visit(child, callback));
}

async function writePackage({ sourcePath, props, name, outputDir }) {
  const fps = 30;
  const assets = collectAssets(props);
  const copiedAssets = await copyAssets(assets, outputDir);
  const timeline = buildTimeline({ sourcePath, props, name, fps, copiedAssets });

  await fs.mkdir(outputDir, { recursive: true });
  await fs.writeFile(path.join(outputDir, "timeline.json"), `${JSON.stringify(timeline, null, 2)}\n`, "utf8");
  await fs.writeFile(path.join(outputDir, "captions.srt"), subtitlesToSrt(props.subtitles ?? [], fps), "utf8");
  await fs.writeFile(path.join(outputDir, "import-guide.md"), buildImportGuide(timeline), "utf8");
  await fs.writeFile(path.join(outputDir, "asset-manifest.json"), `${JSON.stringify(copiedAssets, null, 2)}\n`, "utf8");
}

function pickPackageName(sourcePath, props, index) {
  const fromHook = props.hook?.text ? sanitizeSlug(props.hook.text.split("\n")[0]) : "";
  const base = sanitizeSlug(path.basename(sourcePath, path.extname(sourcePath)));
  return index === 0 ? base || fromHook || "capcut-export" : `${base || fromHook || "capcut-export"}-${index + 1}`;
}

function sanitizeSlug(value) {
  return String(value)
    .replace(/[\\/:*?"<>|]/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 120);
}

function collectAssets(props) {
  const assets = new Set();
  addAsset(assets, props.audioSrc);

  addAsset(assets, props.hook?.imageSrc);
  for (const callout of props.hook?.callouts ?? []) addAsset(assets, callout.imageSrc);

  for (const section of props.sections ?? []) {
    addAsset(assets, section.imageSrc);
    addAsset(assets, section.photoSrc);
    for (const visual of section.visuals ?? []) addAsset(assets, visual.src);
  }

  addAsset(assets, props.cta?.imageSrc1);
  addAsset(assets, props.cta?.imageSrc2);

  for (const cue of props.sfx ?? []) addAsset(assets, cue.src);

  return [...assets].sort();
}

function addAsset(assets, src) {
  if (!src || typeof src !== "string") return;
  assets.add(src.replace(/^\//, ""));
}

async function copyAssets(assets, outputDir) {
  const manifest = [];
  for (const src of assets) {
    const safeRel = src.split(/[\\/]+/).filter(Boolean).join(path.sep);
    const from = path.join(publicRoot, safeRel);
    const toRel = path.join("assets", safeRel);
    const to = path.join(outputDir, toRel);
    const entry = {
      source: src,
      packagePath: toRel.replaceAll(path.sep, "/"),
      absoluteSource: from,
      exists: true,
    };

    try {
      await fs.mkdir(path.dirname(to), { recursive: true });
      await fs.copyFile(from, to);
    } catch (error) {
      entry.exists = false;
      entry.error = error instanceof Error ? error.message : String(error);
      if (!args.includeMissing) {
        console.warn(`Missing asset: ${from}`);
      }
    }

    manifest.push(entry);
  }
  return manifest;
}

function buildTimeline({ sourcePath, props, name, fps, copiedAssets }) {
  const assetMap = new Map(copiedAssets.map((asset) => [asset.source, asset]));
  const totalFrames = Number(props.totalFrames ?? props.durationInFrames ?? inferTotalFrames(props));

  return {
    name,
    source: path.relative(projectRoot, sourcePath).replaceAll(path.sep, "/"),
    exportedAt: new Date().toISOString(),
    fps,
    width: props.isHorizontal ? 1280 : 1080,
    height: props.isHorizontal ? 720 : 1920,
    durationFrames: totalFrames,
    durationSeconds: framesToSeconds(totalFrames, fps),
    capcutNotes: {
      importOrder: ["assets", "audio", "captions.srt"],
      subtitleFile: "captions.srt",
      draftAutomation: "Use timeline.json as the stable contract for cutcli or another CapCut draft tool.",
    },
    tracks: {
      scenes: buildSceneTrack(props, fps, assetMap),
      subtitles: (props.subtitles ?? [])
        .filter((entry) => entry.text)
        .map((entry) => ({
          startFrame: entry.from,
          endFrame: entry.to,
          start: framesToSeconds(entry.from, fps),
          end: framesToSeconds(entry.to, fps),
          text: entry.text,
        })),
      audio: buildAudioTrack(props, fps, assetMap, totalFrames),
      sfx: (props.sfx ?? []).map((cue, index) => ({
        index,
        source: assetFor(cue.src, assetMap),
        startFrame: cue.fromFrame,
        start: framesToSeconds(cue.fromFrame, fps),
        durationFrames: cue.durationFrames ?? totalFrames - cue.fromFrame,
        volume: cue.volume ?? 0.32,
      })),
    },
  };
}

function buildSceneTrack(props, fps, assetMap) {
  const scenes = [];
  if (props.hook) {
    scenes.push({
      type: "hook",
      title: props.hook.text,
      startFrame: 0,
      endFrame: props.hook.durationFrames,
      start: 0,
      end: framesToSeconds(props.hook.durationFrames, fps),
      visual: assetFor(props.hook.imageSrc, assetMap),
      callouts: (props.hook.callouts ?? []).map((callout) => ({
        startFrame: callout.fromFrame,
        start: framesToSeconds(callout.fromFrame, fps),
        text: callout.text,
        visual: assetFor(callout.imageSrc, assetMap),
      })),
    });
  }

  for (const [index, section] of (props.sections ?? []).entries()) {
    scenes.push({
      type: "section",
      index: index + 1,
      title: section.title,
      startFrame: section.fromFrame,
      endFrame: section.fromFrame + section.durationFrames,
      start: framesToSeconds(section.fromFrame, fps),
      end: framesToSeconds(section.fromFrame + section.durationFrames, fps),
      durationFrames: section.durationFrames,
      image: assetFor(section.imageSrc, assetMap),
      photo: assetFor(section.photoSrc, assetMap),
      switchFrame: section.switchFrame ?? null,
      visuals: (section.visuals ?? []).map((visual) => ({
        kind: visual.kind,
        source: assetFor(visual.src, assetMap),
        startFrame: section.fromFrame + visual.fromFrame,
        start: framesToSeconds(section.fromFrame + visual.fromFrame, fps),
        endFrame: visual.toFrame ? section.fromFrame + visual.toFrame : null,
      })),
    });
  }

  if (props.cta) {
    scenes.push({
      type: "cta",
      title: "CTA",
      startFrame: props.cta.fromFrame,
      endFrame: props.cta.fromFrame + props.cta.durationFrames,
      start: framesToSeconds(props.cta.fromFrame, fps),
      end: framesToSeconds(props.cta.fromFrame + props.cta.durationFrames, fps),
      image1: assetFor(props.cta.imageSrc1, assetMap),
      image2: assetFor(props.cta.imageSrc2, assetMap),
      switchFrame: props.cta.switchFrame,
    });
  }

  return scenes;
}

function buildAudioTrack(props, fps, assetMap, totalFrames) {
  if (!props.audioSrc) return null;
  return {
    source: assetFor(props.audioSrc, assetMap),
    startFrame: 0,
    endFrame: totalFrames,
    start: 0,
    end: framesToSeconds(totalFrames, fps),
    volume: 1,
  };
}

function assetFor(src, assetMap) {
  if (!src) return null;
  const normalized = src.replace(/^\//, "");
  const asset = assetMap.get(normalized);
  return asset
    ? {
        source: asset.source,
        packagePath: asset.packagePath,
        exists: asset.exists,
      }
    : {
        source: normalized,
        packagePath: null,
        exists: false,
      };
}

function inferTotalFrames(props) {
  const frameCandidates = [
    props.hook?.durationFrames,
    ...((props.sections ?? []).map((section) => section.fromFrame + section.durationFrames)),
    props.cta ? props.cta.fromFrame + props.cta.durationFrames : 0,
    ...((props.subtitles ?? []).map((entry) => entry.to)),
  ].filter((value) => Number.isFinite(value));

  return Math.max(...frameCandidates, 1);
}

function framesToSeconds(frames, fps) {
  return Number((frames / fps).toFixed(3));
}

function subtitlesToSrt(subtitles, fps) {
  const blocks = subtitles
    .filter((entry) => entry.text)
    .map((entry, index) => {
      return [
        String(index + 1),
        `${formatSrtTime(entry.from, fps)} --> ${formatSrtTime(entry.to, fps)}`,
        entry.text.replace(/\n/g, "\r\n"),
      ].join("\r\n");
    });
  return `${blocks.join("\r\n\r\n")}\r\n`;
}

function formatSrtTime(frames, fps) {
  const totalMs = Math.max(0, Math.round((frames / fps) * 1000));
  const ms = totalMs % 1000;
  const totalSeconds = Math.floor(totalMs / 1000);
  const seconds = totalSeconds % 60;
  const totalMinutes = Math.floor(totalSeconds / 60);
  const minutes = totalMinutes % 60;
  const hours = Math.floor(totalMinutes / 60);
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)},${String(ms).padStart(3, "0")}`;
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function buildImportGuide(timeline) {
  const audio = timeline.tracks.audio?.source?.packagePath ?? "(no main audio)";
  return `# CapCut Import Guide

Package: ${timeline.name}
Duration: ${timeline.durationSeconds}s
Canvas: ${timeline.width}x${timeline.height}

## Files

- Main audio: ${audio}
- Captions: captions.srt
- Timeline metadata: timeline.json
- Assets: assets/

## Stable workflow

1. Open CapCut Desktop or CapCut Web.
2. Create a project with the canvas size above.
3. Import the files under assets/.
4. Place the main audio at 00:00.
5. Import captions.srt.
6. Use timeline.json for scene order, timing, and visual placement.

## Draft automation

timeline.json is the contract for experimental tools such as cutcli or a CapCut MCP server.
Keep this package as the source of truth when a draft tool breaks after a CapCut update.
`;
}
