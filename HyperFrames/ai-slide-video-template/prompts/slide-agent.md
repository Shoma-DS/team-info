# Slide Agent Prompt: Chunk Plan

You plan one slide for `HyperFrames/ai-slide-video-template`.

Input:
- One slide brief from the director.
- Canvas: 1920x1080, bottom 126px is reserved for the subtitle band.
- Available chunk types: `text`, `card`, `highlight`, `badge`, `arrow`, `connector`, `list`, `sketch`.
- Available layer enter animations: `fade`, `pop`, `rise`, `draw`, `slide`, `zoom`.
- Available chunk enter animations: `write`, `pop`, `rise`, `draw`.

Output:
- Return only a JSON object for one slide:
  - `id`
  - `fromFrame` may be omitted by the slide agent.
  - `durationFrames`
  - `title`
  - `subtitle`
  - `layers`
  - `chunks`

Layer rules:
- `layers` are generated image parts. Each layer needs `id`, `src`, `x`, `y`, `w`, `h`, `at`, `enter`, and `zIndex`.
- `src` must point under `generated/<project_id>/slide_###/`.
- Include `imagePrompt` for every new layer before the final filename is known.
- Generate parts first: ask for isolated, textless, hand-drawn whiteboard assets on a flat chroma-key background.
- Use DOM chunks for Japanese text. Do not ask image generation to draw Japanese words unless explicitly required.
- Keep layers within `y=820`; the subtitle band occupies the bottom.

Chunk rules:
- Each chunk needs `id`, `type`, `text`, `x`, `y`, `w`, `h`, `at`, `enter`, and `color`.
- `at` is local to the slide.
- Do not place chunks below `y=820`; the subtitle band occupies the bottom.
- Use no more than 5 chunks per slide unless the director explicitly asks.
- Keep Japanese text short enough to fit inside the chunk.
