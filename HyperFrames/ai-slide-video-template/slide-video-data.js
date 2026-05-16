/**
 * AI slide video template data.
 * AI agents can generate this structure slide by slide, then HyperFrames renders
 * the chunk reveal order from deterministic frame-based state.
 */
window.AI_SLIDE_VIDEO = {
  id: "ai-slide-video-template",
  fps: 30,
  width: 1920,
  height: 1080,
  totalFrames: 2880,
  assetsBase: "generated/demo-layered-slide",
  imageGeneration: {
    mode: "codex-built-in-imagegen",
    strategy: "generate-parts-first",
    sourceSheet: "generated/demo-layered-slide/source/asset-sheet.png",
    note: "Japanese text stays in DOM chunks; generated images are textless diagram parts."
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
      id: "hook",
      fromFrame: 0,
      durationFrames: 360,
      title: "動画編集ソフトを\n開かない動画制作",
      subtitle: "文字や絵が、1個ずつ湧き出す手書き風スライドにする。",
      layers: [
        {
          id: "generated-laptop-gear",
          src: "slide_001/laptop-gear.png",
          alt: "手書きのノートPCと歯車",
          x: 186,
          y: 316,
          w: 430,
          h: 392,
          at: 36,
          enter: "zoom",
          duration: 20,
          rotate: -4,
          opacity: 0.92,
          zIndex: 1
        },
        {
          id: "generated-orange-arrow",
          src: "slide_001/orange-arrow.png",
          alt: "手書きのオレンジ矢印",
          x: 1274,
          y: 236,
          w: 326,
          h: 310,
          at: 76,
          enter: "slide",
          duration: 18,
          fromX: 42,
          fromY: -16,
          rotate: 5,
          zIndex: 2
        },
        {
          id: "generated-yellow-highlight",
          src: "slide_001/yellow-highlight.png",
          alt: "手書きの黄色い強調枠",
          x: 404,
          y: 588,
          w: 1110,
          h: 168,
          at: 118,
          enter: "draw",
          duration: 22,
          fit: "fill",
          opacity: 0.72,
          zIndex: 0
        }
      ],
      chunks: [
        {
          id: "blank-board",
          type: "card",
          text: "",
          x: 640,
          y: 232,
          w: 640,
          h: 220,
          at: 0,
          enter: "draw",
          color: "#172033"
        },
        {
          id: "main-title",
          type: "text",
          text: "動画編集ソフトを\n開かない",
          x: 700,
          y: 274,
          w: 520,
          h: 124,
          at: 18,
          enter: "write",
          fontSize: 60,
          weight: 900,
          color: "#172033"
        },
        {
          id: "orange-arrow",
          type: "arrow",
          text: "作業を\n仕組みに逃がす",
          x: 1304,
          y: 246,
          w: 250,
          h: 264,
          at: 72,
          enter: "rise",
          color: "#f97316"
        },
        {
          id: "bottom-note",
          type: "highlight",
          text: "見る人は「次に何が出るか」を追っている",
          x: 462,
          y: 610,
          w: 996,
          h: 130,
          at: 126,
          enter: "pop",
          color: "#facc15",
          fontSize: 52
        }
      ]
    },
    {
      id: "problem",
      fromFrame: 360,
      durationFrames: 420,
      title: "静止画の問題",
      subtitle: "きれいなスライドでも、画面の中で何も動かないと目が滑る。",
      layers: [
        {
          id: "generated-slide-cards",
          src: "slide_002/slide-cards.png",
          alt: "手書きのスライドカード束",
          x: 206,
          y: 150,
          w: 548,
          h: 428,
          at: 8,
          enter: "pop",
          duration: 20,
          rotate: -2,
          opacity: 0.88,
          zIndex: 0
        },
        {
          id: "generated-problem-arrow",
          src: "slide_001/orange-arrow.png",
          alt: "手書きのオレンジ矢印",
          x: 850,
          y: 118,
          w: 332,
          h: 316,
          at: 62,
          enter: "slide",
          duration: 18,
          fromX: -38,
          fromY: 12,
          rotate: -7,
          opacity: 0.95,
          zIndex: 1
        }
      ],
      chunks: [
        {
          id: "static-slide",
          type: "card",
          text: "静止スライド\n5秒ごと切替",
          x: 300,
          y: 190,
          w: 500,
          h: 210,
          at: 0,
          enter: "pop",
          fontSize: 54,
          color: "#172033"
        },
        {
          id: "eye-slip",
          type: "arrow",
          text: "目が滑る",
          x: 882,
          y: 150,
          w: 230,
          h: 250,
          at: 58,
          enter: "rise",
          color: "#f97316"
        },
        {
          id: "no-preview",
          type: "highlight",
          text: "次に何が出るかの予感が消える",
          x: 454,
          y: 548,
          w: 820,
          h: 118,
          at: 112,
          enter: "write",
          color: "#facc15",
          fontSize: 48
        },
        {
          id: "lesson",
          type: "badge",
          text: "教育系は\n動きで見られる",
          x: 1300,
          y: 462,
          w: 330,
          h: 200,
          at: 182,
          enter: "pop",
          color: "#16a34a"
        }
      ]
    },
    {
      id: "decompose",
      fromFrame: 780,
      durationFrames: 510,
      title: "全体ではなく\n塊を順番に出す",
      subtitle: "タイトル、ボックス、アイコン、矢印をチャンクとして分ける。",
      chunks: [
        {
          id: "chunk-title",
          type: "card",
          text: "① タイトル文字",
          x: 270,
          y: 174,
          w: 410,
          h: 110,
          at: 0,
          enter: "write",
          color: "#172033"
        },
        {
          id: "chunk-box",
          type: "card",
          text: "② ボックス",
          x: 270,
          y: 326,
          w: 410,
          h: 110,
          at: 54,
          enter: "pop",
          color: "#172033"
        },
        {
          id: "chunk-icon",
          type: "card",
          text: "③ アイコン群",
          x: 270,
          y: 478,
          w: 410,
          h: 110,
          at: 108,
          enter: "rise",
          color: "#172033"
        },
        {
          id: "sequence-arrow",
          type: "connector",
          text: "順番だけ決める",
          x: 760,
          y: 333,
          w: 360,
          h: 120,
          at: 160,
          enter: "draw",
          color: "#f97316"
        },
        {
          id: "agent-output",
          type: "sketch",
          text: "slide_03.plan.json",
          x: 1180,
          y: 250,
          w: 460,
          h: 250,
          at: 214,
          enter: "pop",
          color: "#16a34a"
        }
      ]
    },
    {
      id: "parallel",
      fromFrame: 1290,
      durationFrames: 570,
      title: "1スライド1担当で\n並列に計画する",
      subtitle: "各スライドは独立しているので、順序計画を同時に走らせる。",
      chunks: [
        {
          id: "slide-queue",
          type: "list",
          text: "slide 01\nslide 02\nslide 03\nslide 04\nslide 05",
          x: 260,
          y: 184,
          w: 330,
          h: 390,
          at: 0,
          enter: "write",
          color: "#172033"
        },
        {
          id: "agents",
          type: "list",
          text: "agent A\nagent B\nagent C\nagent D\nagent E",
          x: 780,
          y: 184,
          w: 330,
          h: 390,
          at: 86,
          enter: "rise",
          color: "#16a34a"
        },
        {
          id: "parallel-arrow",
          type: "connector",
          text: "同時に投げる",
          x: 610,
          y: 322,
          w: 160,
          h: 110,
          at: 136,
          enter: "draw",
          color: "#f97316"
        },
        {
          id: "time-card",
          type: "highlight",
          text: "1日 → 20分台の下書き",
          x: 1178,
          y: 266,
          w: 470,
          h: 150,
          at: 210,
          enter: "pop",
          color: "#facc15",
          fontSize: 48
        },
        {
          id: "human-polish",
          type: "badge",
          text: "最後は人間が\n30分ほど手詰め",
          x: 1195,
          y: 488,
          w: 430,
          h: 170,
          at: 300,
          enter: "rise",
          color: "#172033"
        }
      ]
    },
    {
      id: "hyperframes",
      fromFrame: 1860,
      durationFrames: 600,
      title: "HyperFramesへの落とし込み",
      subtitle: "AIの計画を data.js に集約し、seek(time) が現在の見た目を決める。",
      chunks: [
        {
          id: "pipeline-input",
          type: "sketch",
          text: "台本\n↓\nスライド分割",
          x: 230,
          y: 220,
          w: 330,
          h: 250,
          at: 0,
          enter: "pop",
          color: "#172033"
        },
        {
          id: "pipeline-plan",
          type: "sketch",
          text: "chunk plan\nJSON",
          x: 642,
          y: 220,
          w: 330,
          h: 250,
          at: 76,
          enter: "rise",
          color: "#16a34a"
        },
        {
          id: "pipeline-hf",
          type: "sketch",
          text: "index.html\n__hf.seek()",
          x: 1054,
          y: 220,
          w: 330,
          h: 250,
          at: 150,
          enter: "pop",
          color: "#f97316"
        },
        {
          id: "pipeline-video",
          type: "sketch",
          text: "render.mp4",
          x: 1466,
          y: 220,
          w: 310,
          h: 250,
          at: 224,
          enter: "rise",
          color: "#172033"
        },
        {
          id: "pipeline-note",
          type: "highlight",
          text: "編集タイムラインではなく、フレームからDOM状態を再計算する",
          x: 360,
          y: 604,
          w: 1200,
          h: 122,
          at: 304,
          enter: "write",
          color: "#facc15",
          fontSize: 44
        }
      ]
    },
    {
      id: "finish",
      fromFrame: 2460,
      durationFrames: 420,
      title: "導入の第一歩",
      subtitle: "このテンプレートを増やし、AI担当が slide plan を並列生成できる形にする。",
      chunks: [
        {
          id: "step1",
          type: "card",
          text: "1. 台本から\nスライド一覧を作る",
          x: 282,
          y: 216,
          w: 410,
          h: 200,
          at: 0,
          enter: "write",
          color: "#172033"
        },
        {
          id: "step2",
          type: "card",
          text: "2. 各スライドを\nチャンク計画へ",
          x: 754,
          y: 216,
          w: 410,
          h: 200,
          at: 80,
          enter: "pop",
          color: "#16a34a"
        },
        {
          id: "step3",
          type: "card",
          text: "3. HyperFramesで\nseek再生",
          x: 1226,
          y: 216,
          w: 410,
          h: 200,
          at: 160,
          enter: "rise",
          color: "#f97316"
        },
        {
          id: "final",
          type: "highlight",
          text: "人間は「何を伝えるか」と最後の見た目確認に集中する",
          x: 380,
          y: 566,
          w: 1160,
          h: 132,
          at: 238,
          enter: "write",
          color: "#facc15",
          fontSize: 48
        }
      ]
    }
  ]
};
