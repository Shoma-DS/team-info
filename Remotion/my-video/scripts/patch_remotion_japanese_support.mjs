import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");

const regexBefore = "^([a-zA-Z0-9-\\u4E00-\\u9FFF])+$";
const regexAfter = "^([a-zA-Z0-9-\\u3005-\\u30FF\\u4E00-\\u9FFF])+$";
const folderErrorBefore =
  "Folder name can only contain a-z, A-Z, 0-9 and -.";
const folderErrorAfter =
  "Folder name can only contain a-z, A-Z, 0-9, Japanese characters and -.";
const compositionErrorBefore =
  "Composition id can only contain a-z, A-Z, 0-9, CJK characters and -.";
const compositionErrorAfter =
  "Composition id can only contain a-z, A-Z, 0-9, Japanese characters and -.";

const filesToPatch = [
  "node_modules/remotion/dist/cjs/validation/validate-folder-name.js",
  "node_modules/remotion/dist/cjs/validation/validate-composition-id.js",
  "node_modules/remotion/dist/esm/index.mjs",
];

const replaceIfNeeded = (source, before, after) => {
  if (source.includes(after)) {
    return source;
  }

  return source.replaceAll(before, after);
};

const patchFile = async (relativePath) => {
  const absolutePath = path.join(projectRoot, relativePath);
  const original = await readFile(absolutePath, "utf8");

  let patched = replaceIfNeeded(original, regexBefore, regexAfter);
  patched = replaceIfNeeded(patched, folderErrorBefore, folderErrorAfter);
  patched = replaceIfNeeded(
    patched,
    compositionErrorBefore,
    compositionErrorAfter,
  );

  if (patched !== original) {
    await writeFile(absolutePath, patched);
    return { relativePath, status: "patched" };
  }

  return { relativePath, status: "already-patched" };
};

const main = async () => {
  const results = await Promise.all(filesToPatch.map((file) => patchFile(file)));
  const summary = results
    .map(({ relativePath, status }) => `${status}: ${relativePath}`)
    .join("\n");

  console.log(summary);
};

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
