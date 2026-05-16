---
name: hyperframes-slide-video-qa
description: HyperFramesで、完成スライド画像を先に作ってからPNGパーツへ分解し、順番に表示するAIスライド動画を作る・直す・検証するときに使う。SVG禁止、黒字幕帯、マスク漏れ、未登場パーツの見え隠れ、スクショ確認まで扱う。
---

# HyperFrames Slide Video QA

## 役割
- HyperFrames の AI スライド動画で、完成スライドPNGを正としてパーツ分解し、順番に出す動画を作る。
- パーツのマスク漏れ、黒い矩形、次パーツの見え隠れ、字幕帯の扱いを必ず検証する。
- ユーザーから「直ってない」「黒くなっている」「マスクで見切れている」と言われたら、まずこのスキルで再検証する。

## トーク履歴から固定した指示
- 基本実装先は `HyperFrames`。既存テンプレを育て、新テンプレを乱立しない。
- 参考動画がある場合は、NotebookLM などで文字起こしを取得し、ブラウザは音声ゼロで開いて1秒ごとの見た目をスクショ確認する。
- 参考動画の仕組みを学んでから、repo の構成に合わせて導入計画と実装へ落とす。
- まず1枚の完成スライド画像を作り、その完成配置を正としてPNGパーツへ分解する。
- パーツ先行生成は使わない。配置バランスが崩れるため、完成スライド先行方式を優先する。
- SVGは作らない。SVG由来の暫定画像も残さない。
- 画像生成API、APIキー、OpenAI API 呼び出しは使わない。画像が必要なら Codex/ChatGPT の組み込み画像生成を使う。
- 画面内の日本語は原則、完成スライド画像から切り出した画像パーツとして扱う。
- 黒い字幕帯は、文字なしの帯だけを完成スライドに含める。字幕文字は HyperFrames のDOMテキストで重ねる。
- パーツのマスクは「画像サイズ」ではなく「実際に見えている手描き要素」に合わせる。
- 修正後は必ずスクショを取り、目視で確認してから「直った」と言う。

## 制作フロー
1. `.dev-mode` と `git status --short` を確認する。大きく作り直す前は、ユーザーが求めた場合に rollback 用コミットを作る。
2. 参考動画がある場合は、文字起こしと秒単位スクショで、構成・出現順・画風・字幕処理を先に確認する。
3. `source/full-slide-with-subtitle-band.png` を正とし、`source/full-slide.png` は黒字幕帯を除いた確認用として扱う。
4. `generated/<project_id>/slide_###/parts/` に、完成画像から `magick` でPNGパーツを切り出す。
5. 透明化は背景色を雑に抜くだけで終わらせない。隣接パーツが近い箇所は、残す領域だけを白で描くホワイトリスト型 alpha mask を使う。
6. `slide-video-data.js` の `x/y/w/h` は、切り出し元の source 座標と同じ値にする。拡大縮小で位置合わせしない。
7. `index.html` の画像レイヤーは追加 `drop-shadow` を切る。元画像に含まれる手描き影だけを使う。
8. on-slide text は `layers` で表示し、`chunks` は黒帯字幕以外に使わない。

## マスク作成ルール
- crop は大きめに取ってよいが、最終PNGの不透明領域はパーツ本体だけにする。
- 隣の要素が近い場合は、減算型の「消すマスク」より、残す範囲だけを指定するホワイトリスト型マスクを優先する。
- 透明PNGを単体表示すると透明部分が黒く見えることがある。単体PNGだけで合否判定せず、必ず HyperFrames 合成スクショで見る。
- `object-fit: contain` で座標がずれる可能性があるため、crop サイズと `w/h` を一致させる。
- 黒字幕帯や下の黄色帯が他パーツへ混ざる場合は、そのパーツのcropを狭めるか、マスクで明示的に除外する。

## 必須チェックリスト
- 完成スライドは16:9で、下部に文字なし黒字幕帯がある。
- パーツ一覧に SVG がない。
- `slide-video-data.js` の `imageGeneration.strategy` は `full-slide-then-decompose`。
- 画面内タイトル・本文・強調文字は画像パーツで、黒帯字幕だけDOMテキスト。
- 各 `parts/*.png` の不透明領域に、未登場の隣接パーツが混ざっていない。
- 2秒付近で左パーツだけが見え、中央カードや下帯の断片が出ていない。
- 3秒付近で矢印と中央カードに余計な縦線・黒矩形がない。
- 5秒付近で右上メモに右カードの線が混ざっていない。
- 6秒付近で右カードと矢印に中央カード端や黄色下帯が混ざっていない。
- 8秒以降で下部黄色ノートに黒字幕帯が混ざっていない。
- 最終フレームが完成スライドと同じ配置に見える。

## 検証コマンド
HyperFrames CLI がテンプレ側で見つからない場合は、既存の HyperFrames プロジェクトを `--prefix` にして明示実行する。

```bash
npx --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" hyperframes snapshot \
  --project "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template" \
  --at 1,2,3,4,5,6,7,8,10 \
  --timeout 12000
```

```bash
npx --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" hyperframes inspect \
  --project "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template" \
  --at 0,2,4,6,8,10 \
  --timeout 12000
```

```bash
npx --prefix "$TEAM_INFO_ROOT/HyperFrames/tenshoku-short-20260416" hyperframes lint \
  --project "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template"
```

PNG単体の不透明領域確認:

```bash
for f in "$TEAM_INFO_ROOT/HyperFrames/ai-slide-video-template/generated/decomposed-full-slide-demo/slide_001/parts/"*.png; do
  printf '%s ' "$(basename "$f")"
  magick "$f" -alpha extract -trim -format '%wx%h%O\n' info: 2>/dev/null || true
done
```

## 合格基準
- `hyperframes lint` が 0 errors / 0 warnings。
- `hyperframes inspect` が 0 layout issues。
- 指定秒数の snapshot をすべて目視し、未登場パーツ、黒矩形、マスク欠け、余分な影がない。
- ユーザーに見せる前に、問題のあった秒数のスクショを自分で開いて確認している。
