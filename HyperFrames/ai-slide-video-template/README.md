# AI Slide Video Template

HyperFrames で「手書き風スライド動画」を作るための最小テンプレートです。YouTube で確認した構成に合わせ、動画編集タイムラインではなく `slide-video-data.js` のチャンク計画から `window.__hf.seek()` が現在フレームの見た目を再計算します。

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
- `chunks` は文字、カード、矢印、ハイライト、スケッチ風ボックスなどの表示単位。
- `layers` は画像生成した文字なしパーツ。背景、図形、人物、矢印、強調枠などを最初から別画像として作り、`at` と `enter` で順番に出す。
- 1スライド1担当でAIエージェントへ並列に投げ、各担当はそのスライドだけの `chunks` を返す。
- 統合担当が `fromFrame` と `totalFrames` を確定し、`slide-video-data.js` にまとめる。
- HyperFrames 側は `seek(time)` でフレームからDOM状態を決めるため、動画編集ソフトのキー フレーム操作を持ち込まない。

## 画像生成レイヤー

- 生成画像は `generated/<project_id>/slide_###/` に置く。
- このサンプルでは `generated/demo-layered-slide/source/asset-sheet.png` を Codex/ChatGPT の画像生成で作り、4つの透明PNGへ切り出している。
- 日本語テキストは画像に焼き込まず、`chunks` 側で描画する。AI画像内の日本語崩れを避け、修正もDOMだけで済ませるため。
- 透明パーツが必要な場合は、平坦なクロマキー背景で生成し、ローカルで背景を抜いてから `layers[].src` に指定する。
- `layers[].enter` は `fade`、`pop`、`rise`、`draw`、`slide`、`zoom` に対応する。

レイヤー例:

```js
{
  id: "generated-orange-arrow",
  src: "slide_001/orange-arrow.png",
  x: 1274,
  y: 132,
  w: 360,
  h: 342,
  at: 76,
  enter: "slide",
  fromX: 42,
  fromY: -16,
  zIndex: 2
}
```

## ファイル構成

- `index.html`: HyperFrames composition。データを読み込み、現在フレームのスライドとチャンク状態を描画する。
- `slide-video-data.js`: AIが生成・更新する動画構成データ。`layers` と `chunks` を同じフレーム基準で扱う。
- `generated/demo-layered-slide/`: サンプルの生成画像アセット。
- `prompts/director.md`: 台本からスライド一覧を作る担当向け。
- `prompts/slide-agent.md`: 1スライド分の画像レイヤーとチャンク計画を作る担当向け。
- `prompts/integrator.md`: 複数スライド計画を統合してデータ化する担当向け。

## 参考動画から反映した見た目

- 16:9 横長、白い紙/ホワイトボード風背景。
- 濃い手書き線、オレンジ・黄色・緑のアクセント。
- 文字、カード、矢印、図解が順番に出てくる。
- 下部に黒帯字幕を置き、本文の進行と画面の動きを同期する。
- 完成動画を一発生成するより、スライド内要素をチャンクに分けて順序計画する。
