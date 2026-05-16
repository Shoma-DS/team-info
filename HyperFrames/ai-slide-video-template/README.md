# AI Slide Video Template

HyperFrames で「手書き風スライド動画」を作るための最小テンプレートです。完成スライド画像を先に作り、その画像をパーツへ分解して、`slide-video-data.js` のレイヤー計画から `window.__hf.seek()` が現在フレームの見た目を再計算します。

## 使い方

```bash
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template" install
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template" run inspect
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template" run preview
```

レンダー:

```bash
npm --prefix "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template" run render
```

出力先:

```text
$TEAM_INFO_ROOT/outputs/hyperframes/ai-slide-video-template.mp4
```

## 導入方針

- 台本をスライドへ分割し、各スライドを `title`、`subtitle`、`chunks` に分ける。
- まず完成状態のスライド画像を1枚生成する。下部には文字なしの黒い字幕帯を入れ、その前提で画面上部の配置を決める。
- `layers` は完成スライド画像から切り出したパーツ。テキストも絵として切り出し、`at` と `enter` で順番に出す。
- 黒い字幕帯も画像レイヤーとして扱うが、字幕文字は文字起こし台本からHyperFramesのテキストで重ねる。
- 1スライド1担当でAIエージェントへ並列に投げ、各担当は完成画像と切り出し計画を返す。
- 統合担当が `fromFrame` と `totalFrames` を確定し、`slide-video-data.js` にまとめる。
- HyperFrames 側は `seek(time)` でフレームからDOM状態を決めるため、動画編集ソフトのキー フレーム操作を持ち込まない。

## 画像生成レイヤー

- 完成スライド画像は `generated/<project_id>/slide_###/source/full-slide.png` に置く。
- 分解したパーツは `generated/<project_id>/slide_###/parts/` に置く。
- このサンプルでは `generated/decomposed-full-slide-demo/slide_001/source/full-slide.png` を Codex/ChatGPT の画像生成で作り、そこから6つのPNGへ切り出している。
- 字幕帯は `parts/subtitle-band.png` として別パーツにし、`source/full-slide-with-subtitle-band.png` を全体確認用に置く。
- 画面内の日本語テキストはDOMで描かず、完成画像から切り出した画像レイヤーとして表示する。
- 字幕帯の中の文字だけはDOMで描く。字幕は文字起こし台本から流し込む前提。
- `layers[].enter` は `fade`、`pop`、`rise`、`draw`、`slide`、`zoom`、`wipe` に対応する。
- `wipe` は `direction` で `left-to-right`、`top-to-bottom`、`right-to-left`、`bottom-to-top` を指定できる。

レイヤー例:

```js
{
  id: "subtitle-band",
  src: "parts/subtitle-band.png",
  x: 0,
  y: 924,
  w: 1920,
  h: 156,
  at: 0,
  enter: "fade",
  fit: "fill",
  shadow: false,
  zIndex: 0
}
```

## ファイル構成

- `index.html`: HyperFrames composition。データを読み込み、現在フレームのスライドとチャンク状態を描画する。
- `slide-video-data.js`: AIが生成・更新する動画構成データ。完成画像から切り出した `layers` を同じフレーム基準で扱う。
- `generated/demo-layered-slide/`: サンプルの生成画像アセット。
- `generated/decomposed-full-slide-demo/`: 完成スライド先行方式のサンプル。
- `prompts/director.md`: 台本からスライド一覧を作る担当向け。
- `prompts/slide-agent.md`: 1スライド分の完成画像と切り出し計画を作る担当向け。
- `prompts/integrator.md`: 複数スライド計画を統合してデータ化する担当向け。

## 参考動画から反映した見た目

- 16:9 横長、白い紙/ホワイトボード風背景。
- 濃い手書き線、オレンジ・黄色・緑のアクセント。
- 文字、カード、矢印、図解が順番に出てくる。
- 下部に黒帯字幕を置き、本文の進行と画面の動きを同期する。
- 完成動画を一発生成するより、スライド内要素をチャンクに分けて順序計画する。
