---
name: canva-slide-design-extender
description: Extend existing Canva presentations from a template or design link while preserving the original visual system. Use when a user wants new slides added in Canva without breaking layout, typography, color, spacing, or component patterns.
---

# Canva Slide Design Extender

## Goal
- Canva の既存デザインやテンプレを土台にして、同じ見た目のまま新しいスライドを追加する。
- 色、余白、タイポグラフィ、図版スタイル、ページ構成を壊さずに資料を増築する。
- 「ゼロから新デザインを作る」ではなく「既存デザインを正しく継承する」ことを最優先にする。

## When To Use
- Canva のテンプレリンクを渡されて、そのテンプレで新しいページを作りたいとき。
- 既存の Canva 資料リンクを渡されて、同じトンマナで続きを作りたいとき。
- 営業資料、会社紹介、提案書、採用資料、SNSスライドなどで既存の見た目を厳密に維持したいとき。
- 完成した Canva スライドを動画化したい場合は、仕上げ後に `.agent/skills/canva/canva-slideshow-video/SKILL.md` を使う。

## Inputs
- Canva のデザインリンク、テンプレリンク、または Brand Template 情報
- 追加したいページ数と各ページの目的
- 元になる文章、箇条書き、画像、ロゴ、図表データ
- 同一デッキに追記するのか、新しいデッキを同デザインで作るのか

## Workflow

### Phase 1: 入力を分類する
1. まず入力がどの種類かを判定する。
- 既存デザインの編集リンク
- 公開テンプレの複製元リンク
- Brand Template
- Canva 外の参考資料しかないケース
2. 作業モードを決める。
- `extend-existing`: 同じデッキにページ追加
- `new-deck-from-template`: テンプレから新規デッキ作成
- `brand-template-autofill`: Brand Template から量産
3. 公開テンプレしかなく編集権限がない場合は、先に Canva 上で複製した作業用デザインを基準にする。

### Phase 2: デザインの骨格を読む
1. 参照ページを最低 3 種類は拾う。
- 表紙
- 通常本文
- 強調ページまたは CTA
2. 次の共通ルールを抽出する。
- ページ比率と余白
- 見出しサイズ、本文サイズ、行間
- 配色ルール
- 写真・イラスト・アイコンの扱い
- カード、吹き出し、線、背景装飾の形
- チャートや表のスタイル
3. ページをレイアウト archetype に分ける。

例:
- cover
- section-intro
- single-message
- three-cards
- comparison
- quote
- cta

### Phase 3: 追加ページの設計を先に固定する
1. 追加する各ページを、既存 archetype のどれで作るか先に割り当てる。
2. 近い archetype があるなら blank page から作らない。
3. 新しい型が必要でも、既存 2 ページの中間として組み立てる。
4. 1ページに情報が入り切らない場合は、無理に縮めずページを増やす。

推奨の進め方:
- ページ目的を 1 行で定義
- 見出しを 1 つ決める
- 本文は 3 から 5 点までに圧縮
- 画像や図が必要なら既存ページの画像枠ルールを流用

### Phase 4: Canva 上でページを増築する
1. 既存デザインを編集するときは、最も近い参照ページを複製してから編集する。
2. 編集対象は原則として中身だけに限定する。
- テキスト
- 画像
- 数値
- アイコン
3. できるだけ変えないもの:
- フォント種類
- 基本サイズ体系
- 配置グリッド
- 角丸
- シャドウ
- 線幅
- アニメーション方針
4. 画像差し替え時は、同じマスクやアスペクト比を維持する。
5. チャートや表は既存ページを複製してデータだけ差し替える。

### Phase 5: Canva API を使う補助ルート
Canva Connect API は補助用途として使う。主目的は「既存デザインを維持したまま Canva エディタへ正しく入ること」であり、自由なレイアウト再構築ではない。

使える補助:
- 既存デザイン検索
- 新規デザイン作成
- `edit_url` を取得して Canva editor へ入る
- ページサムネイル取得
- Brand Template の autofill

ローカルの関連スクリプト:

```bash
python "$TEAM_INFO_ROOT/mcp-servers/canva_auth.py"
python "$TEAM_INFO_ROOT/mcp-servers/canva_slideshow.py" --script "台本.md" --theme "テーマ名"
```

`canva_slideshow.py` は認証済み Canva 連携やエクスポート処理の参考には使えるが、既存資料の見た目維持を主目的にした増築フローの主役にはしない。

API ノート:
- Canva Connect API の `Create design` は新規デザインを作成し、`edit_url` を返せる。
- `List designs` で既存デザインを探せる。
- `Get design pages` でページごとのサムネイルを取得できるが、preview API として扱う。
- `Autofill` は Canva Enterprise の Brand Template 前提。
- 正確な見た目維持が必要な通常案件では、最終編集は Canva editor 上のページ複製ベースを標準にする。

### Phase 6: Brand Template autofill を使う条件
以下を満たす場合だけ autofill を優先する。
- Canva Enterprise を利用している
- Brand Template に autofill 用フィールドが仕込まれている
- ページ量産の変数が明確

向いている例:
- 商品紹介カード量産
- 店舗別資料
- 採用職種別資料
- 顧客別提案書の量産

向かない例:
- ページごとの自由度が高い企画資料
- レイアウト調整が頻繁に必要な提案資料
- 図解や複雑な比較表が多い資料

## Guardrails
- 近い既存ページがあるのに blank page から作らない。
- フォントファミリーを勝手に増やさない。
- 既存より小さい文字へ逃げすぎない。詰まるならページ分割を優先する。
- 配色は既存ページから採取した色だけで回す。
- アイコン、写真、図版の角丸や枠線ルールを混在させない。
- 図表はスタイルを再発明せず、既存図表を複製して差し替える。
- 同一資料内で見出し位置、ページ番号、ロゴ位置をぶらさない。
- 既存テンプレの情報密度が高い場合でも、無理に 1 ページへ押し込まない。

## Quality Check
- 追加ページだけ見ても、元からそのデッキに含まれていたように見えるか。
- 見出しサイズ、余白、整列が既存ページと揃っているか。
- テキスト overflow や不自然な改行がないか。
- 画像のトリミングが不自然でないか。
- カード、ボタン、装飾の角丸・線・影が既存と一致しているか。
- 既存資料の前後に挿入して読んだとき、流れが自然か。

## Verification
1. 既存 Canva デザインかテンプレを 1 件使う。
2. 追加ページを最低 2 ページ作る。
3. 参照ページと新規ページを並べ、色・余白・文字サイズ・コンポーネント形状が一致しているか確認する。
4. API 補助ルートを使う場合は、認証、デザイン特定、`edit_url` 到達または autofill 完了まで確認する。
