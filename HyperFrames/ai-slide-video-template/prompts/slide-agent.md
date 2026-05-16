# Slide Agent Prompt: Completed Slide Decomposition Plan

You plan one slide for `HyperFrames/ai-slide-video-template`.

Input:
- One slide brief from the director.
- Canvas: 1920x1080, with a textless generated black subtitle band at the bottom.
- Available layer enter animations: `fade`, `pop`, `rise`, `draw`, `slide`, `zoom`, `wipe`.
- Available wipe directions: `left-to-right`, `top-to-bottom`, `right-to-left`, `bottom-to-top`.

Output:
- Return only a JSON object for one slide:
  - `id`
  - `fromFrame` may be omitted by the slide agent.
  - `durationFrames`
  - `subtitle`
  - `sourceImage`
  - `layers`
  - `chunks` as an empty array unless the director explicitly asks for DOM chunks.

Layer rules:
- First create one completed slide image with the textless black subtitle band already visible at the bottom.
- Crop layers from that completed image so the layout stays fixed.
- `layers` are cropped image parts. Each layer needs `id`, `src`, `x`, `y`, `w`, `h`, `at`, `enter`, and `zIndex`.
- `src` must point under `generated/<project_id>/slide_###/parts/`.
- Text layers are image layers. Use `wipe` for handwritten text reveals.
- Add one `subtitle-band` image layer from the completed image, or from a matching generated band asset.
- Keep all main visual layers above the subtitle band; for the sample, the band starts at `y=924`.
- Do not put any text inside the black subtitle band image. Caption text is rendered later by HyperFrames from the transcript.
- `at` is local to the slide.
