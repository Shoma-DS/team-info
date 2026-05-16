# Integrator Prompt: Merge Slide Plans

You merge director and slide-agent output into `slide-video-data.js`.

Tasks:
- Assign each slide a cumulative `fromFrame`.
- Keep `totalFrames` equal to the sum of all slide durations.
- Set `assetsBase` to the completed slide folder, for example `generated/decomposed-full-slide-demo/slide_001`.
- Keep the completed source image at `source/full-slide.png`.
- Keep the final full-frame reference with the black subtitle band at `source/full-slide-with-subtitle-band.png`.
- Add the textless subtitle band as `parts/subtitle-band.png`.
- Replace crop placeholders with final `parts/*.png` paths.
- Verify no layer or chunk overlaps the subtitle band.
- Normalize colors to the template palette unless the director specifies otherwise.
- Keep the structure compatible with `window.AI_SLIDE_VIDEO`.
- Preserve the completed-image layout: do not re-place parts by eye after cropping.
- Use image layers for all visible on-slide text.
- Render only subtitle text as DOM over the generated black band.

Acceptance:
- `npm --prefix "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template" run inspect` can load the composition.
- The first, middle, and final frames show visible image layers.
- Generated image layers load from the workspace, not from `$CODEX_HOME`.
- The final frame visually matches `source/full-slide.png`.
- The bottom black subtitle band is present without baked-in text, and DOM subtitle text sits on top.
