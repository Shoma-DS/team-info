# Integrator Prompt: Merge Slide Plans

You merge director and slide-agent output into `slide-video-data.js`.

Tasks:
- Assign each slide a cumulative `fromFrame`.
- Keep `totalFrames` equal to the sum of all slide durations.
- Set `assetsBase` to the generated asset project folder, for example `generated/demo-layered-slide`.
- Replace layer `imagePrompt` placeholders with final `src` paths after assets are generated and cropped.
- Verify no layer or chunk overlaps the subtitle band.
- Normalize colors to the template palette unless the director specifies otherwise.
- Keep the structure compatible with `window.AI_SLIDE_VIDEO`.
- Preserve the separation of concerns: image layers are textless visual parts, chunks carry Japanese text and simple DOM shapes.

Acceptance:
- `npm --prefix "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template" run inspect` can load the composition.
- The first, middle, and final slides all show visible chunks.
- Generated image layers load from the workspace, not from `$CODEX_HOME`.
- Text does not overflow its intended card or badge.
