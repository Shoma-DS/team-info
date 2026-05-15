/**
 * Tenshoku HyperFrames data.
 * Remotion の TenshokuShort20260416 と同じ尺、素材、字幕、SFX を
 * HTML Composition 側から参照しやすい構造にまとめる。
 */
window.TENSHOKU_VIDEO = {
  id: "tenshoku-short-20260416",
  fps: 30,
  width: 1080,
  height: 1920,
  totalFrames: 2394,
  assetsBase: "remotion-public/viral/転職ショート_20260416",
  audioBase: "remotion-public/audio/転職ショート_20260416",
  narration: "remotion-public/audio/転職ショート_20260416/narration.wav",
  hook: {
    fromFrame: 0,
    durationFrames: 240,
    text: "優秀な人が黙って去る会社\nの特徴3選",
    image: "hook.png",
    callouts: [
      {
        fromFrame: 118,
        text: "一つでも当てはまったら\n今の会社は危険かも",
        image: "hook_illust.png"
      }
    ]
  },
  sections: [
    {
      fromFrame: 240,
      durationFrames: 665,
      title: "① 現場の意見が完全スルーされる",
      visuals: [
        { fromFrame: 0, kind: "illustration", src: "s1.png" },
        { fromFrame: 77, kind: "photo", src: "p1.png" },
        { fromFrame: 238, kind: "illustration", src: "illust_mushi_business.png" },
        { fromFrame: 387, kind: "illustration", src: "illust_kazetooshi_bad.png" },
        { fromFrame: 506, kind: "illustration", src: "illust_jinzai_hikinuki.png" }
      ]
    },
    {
      fromFrame: 905,
      durationFrames: 605,
      title: "② 頑張った分だけ損をする評価",
      visuals: [
        { fromFrame: 0, kind: "illustration", src: "s2.png" },
        { fromFrame: 72, kind: "photo", src: "p2.png" },
        { fromFrame: 173, kind: "illustration", src: "s2.png" },
        { fromFrame: 319, kind: "illustration", src: "illust_kazetooshi_bad.png" },
        { fromFrame: 460, kind: "illustration", src: "illust_jinzai_hikinuki.png" }
      ]
    },
    {
      fromFrame: 1510,
      durationFrames: 600,
      title: "③ 尊敬できる上司が一人もいない",
      visuals: [
        { fromFrame: 0, kind: "illustration", src: "s3.png" },
        { fromFrame: 77, kind: "photo", src: "p3.png" },
        { fromFrame: 213, kind: "illustration", src: "illust_joushi_buka_men.jpg" },
        { fromFrame: 335, kind: "illustration", src: "s3.png" },
        { fromFrame: 466, kind: "illustration", src: "illust_jinzai_hikinuki.png" }
      ]
    }
  ],
  cta: {
    fromFrame: 2110,
    durationFrames: 284,
    switchFrame: 138,
    image1: "cta.png",
    image2: "cta_alt.png"
  },
  sfx: [
    { fromFrame: 0, src: "sfx/logo-animation2.mp3", volume: 0.12 },
    { fromFrame: 118, src: "sfx/cute-motion1.mp3", volume: 0.08 },
    { fromFrame: 240, src: "sfx/papa1.mp3", volume: 0.06 },
    { fromFrame: 905, src: "sfx/nyu3.mp3", volume: 0.06 },
    { fromFrame: 1510, src: "sfx/papa1.mp3", volume: 0.06 },
    { fromFrame: 2110, src: "sfx/cute-motion1.mp3", volume: 0.06 }
  ],
  subtitles: [
    { from: 3, to: 103, text: "" },
    { from: 103, to: 236, text: "" },
    { from: 245, to: 317, text: "" },
    { from: 317, to: 397, text: "優秀な人は常に\n「より良くしたい」" },
    { from: 397, to: 478, text: "そう思って\n改善案を出します。" },
    { from: 478, to: 552, text: "でも、それを\n「前例がない」" },
    { from: 552, to: 627, text: "「検討する」と\n流し続ける会社。" },
    { from: 627, to: 686, text: "本来、意見を\n求めるなら" },
    { from: 686, to: 746, text: "実行する責任が\n伴うはずです。" },
    { from: 746, to: 824, text: "「言っても無駄だ」\nと悟ったとき" },
    { from: 824, to: 902, text: "優秀な人は\n静かに席を立ちます。" },
    { from: 911, to: 977, text: "" },
    { from: 977, to: 1028, text: "優秀な人にばかり\n仕事が集中し、" },
    { from: 1028, to: 1078, text: "評価は\n横並び。" },
    { from: 1078, to: 1151, text: "「君ならできる」\nという言葉が、" },
    { from: 1151, to: 1224, text: "ただの押し付けに\nなっている環境。" },
    { from: 1224, to: 1294, text: "これでは頑張るほど\n疲弊し、" },
    { from: 1294, to: 1365, text: "モチベーションが\n削られるだけです。" },
    { from: 1365, to: 1435, text: "会社が不公平に\n甘えていると、" },
    { from: 1435, to: 1506, text: "実力のある人から\n抜けていきます。" },
    { from: 1515, to: 1587, text: "" },
    { from: 1587, to: 1655, text: "「この人のように\nなりたい」と" },
    { from: 1655, to: 1723, text: "思えるロールモデルが\nいない。" },
    { from: 1723, to: 1764, text: "上にいるのが、" },
    { from: 1764, to: 1805, text: "保身ばかりの\n人間や、" },
    { from: 1805, to: 1845, text: "指示待ちの\n人間。" },
    { from: 1845, to: 1889, text: "優秀な人は、" },
    { from: 1889, to: 1932, text: "自分の\n「未来の姿」を見て" },
    { from: 1932, to: 1976, text: "転職を\n決意します。" },
    { from: 1976, to: 2041, text: "尊敬が\n消えた瞬間、" },
    { from: 2041, to: 2106, text: "そこはもう\n居場所ではなくなる。" },
    { from: 2116, to: 2160, text: "こういう会社は" },
    { from: 2160, to: 2204, text: "仕組みが\n変わらない限り、" },
    { from: 2204, to: 2248, text: "状況は\n変わりません。" },
    { from: 2248, to: 2296, text: "ぜひ保存して、" },
    { from: 2296, to: 2344, text: "自分の環境を\n見直し、" },
    { from: 2344, to: 2391, text: "より良い未来を\n目指してください。" }
  ]
};
