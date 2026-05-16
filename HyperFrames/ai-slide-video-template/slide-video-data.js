/**
 * AI slide video template data.
 * This version uses one complete generated slide as the source of truth, then
 * replays cropped image parts in the same positions so the layout does not drift.
 */
window.AI_SLIDE_VIDEO = {
  id: "ai-slide-video-template",
  fps: 30,
  width: 1920,
  height: 1080,
  totalFrames: 360,
  assetsBase: "generated/decomposed-full-slide-demo/slide_001",
  imageGeneration: {
    mode: "codex-built-in-imagegen",
    strategy: "full-slide-then-decompose",
    sourceImage: "generated/decomposed-full-slide-demo/slide_001/source/full-slide-with-subtitle-band.png",
    contentSourceImage: "generated/decomposed-full-slide-demo/slide_001/source/full-slide.png",
    sourceOriginal: "generated/decomposed-full-slide-demo/slide_001/source/full-slide-original.png",
    subtitleBand: "generated/decomposed-full-slide-demo/slide_001/parts/subtitle-band.png",
    note: "All visible on-slide copy is cropped from the generated slide image. The subtitle band is also an image layer, but its text is rendered by HyperFrames from the transcript."
  },
  style: {
    background: "#fffdf8",
    ink: "#172033",
    mutedInk: "#475569",
    accent: "#f97316",
    accent2: "#16a34a",
    accent3: "#facc15",
    subtitleBg: "#050505",
    subtitleText: "#ffffff"
  },
  slides: [
    {
      id: "decomposed-full-slide",
      fromFrame: 0,
      durationFrames: 360,
      title: "",
      subtitle: "完成スライドを先に作り、その配置のまま画像パーツとして順番に出す。",
      sourceImage: "source/full-slide-with-subtitle-band.png",
      layers: [
        {
          id: "subtitle-band",
          src: "parts/subtitle-band.png",
          alt: "文字なしの黒い字幕帯",
          x: 0,
          y: 924,
          w: 1920,
          h: 156,
          at: 0,
          enter: "fade",
          duration: 1,
          fit: "fill",
          shadow: false,
          zIndex: 50
        },
        {
          id: "title",
          src: "parts/title.png",
          alt: "完成スライドを先に作る",
          x: 255,
          y: 25,
          w: 1410,
          h: 215,
          at: 0,
          enter: "wipe",
          direction: "left-to-right",
          duration: 24,
          zIndex: 2
        },
        {
          id: "laptop-idea",
          src: "parts/laptop-idea.png",
          alt: "AIのアイデアを図解するノートパソコン",
          x: 15,
          y: 180,
          w: 520,
          h: 640,
          at: 36,
          enter: "zoom",
          duration: 18,
          zIndex: 1
        },
        {
          id: "left-arrow",
          src: "parts/left-arrow.png",
          alt: "中央カードへ向かう矢印",
          x: 410,
          y: 430,
          w: 140,
          h: 150,
          at: 60,
          enter: "draw",
          direction: "left-to-right",
          duration: 16,
          zIndex: 2
        },
        {
          id: "main-card",
          src: "parts/main-card.png",
          alt: "配置を決めてからパーツに分解",
          x: 555,
          y: 245,
          w: 785,
          h: 515,
          at: 72,
          enter: "wipe",
          direction: "top-to-bottom",
          duration: 30,
          zIndex: 3
        },
        {
          id: "side-note",
          src: "parts/side-note.png",
          alt: "作った絵を切り出す",
          x: 1425,
          y: 245,
          w: 430,
          h: 205,
          at: 124,
          enter: "wipe",
          direction: "left-to-right",
          duration: 24,
          zIndex: 4
        },
        {
          id: "arrow-cards",
          src: "parts/arrow-cards.png",
          alt: "矢印とスライドカード",
          x: 1340,
          y: 430,
          w: 555,
          h: 355,
          at: 156,
          enter: "draw",
          direction: "left-to-right",
          duration: 24,
          zIndex: 2
        },
        {
          id: "bottom-note",
          src: "parts/bottom-note.png",
          alt: "文字も絵として切り出す",
          x: 420,
          y: 770,
          w: 1110,
          h: 150,
          at: 210,
          enter: "wipe",
          direction: "left-to-right",
          duration: 30,
          zIndex: 5
        }
      ],
      chunks: []
    }
  ]
};
