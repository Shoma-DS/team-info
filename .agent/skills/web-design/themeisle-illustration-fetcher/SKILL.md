---
name: themeisle-illustration-fetcher
description: Find, download, and integrate illustrations from Themeisle Illustrations into web projects while preserving a consistent visual style. Use when building websites that need modern PNG/SVG illustrations for hero sections, feature blocks, cards, or onboarding UI.
---

# Themeisle Illustration Fetcher

## Goal
- Themeisle Illustrations から PNG / SVG 素材を選び、Webサイトへ組み込む。
- ヒーロー、特徴紹介、空状態、説明セクション向けの大きめイラストを自然に使う。
- 既存のレイアウトを壊さず、画像サイズとスタイルを統一する。
- 汎用の「ちょうどいいイラストに差し替えたい」という依頼では、このスキルを第一候補にする。

## Source Choice Rule
- 画像ダウンロード系スキル候補が複数ある場合は、自動で決めない。
- `tyoudoii-illust-fetcher` も候補になるなら、必ずユーザーにどちらを使うか確認する。
目安:
- 日本語サイト向け、ゆるめ、親しみやすい国内イラスト: `tyoudoii-illust-fetcher`
- SaaS / LP / スタートアップ寄り、SVGで拡張しやすい海外テイスト: `themeisle-illustration-fetcher`

## When To Use
- 汎用的な「ちょうどいいイラスト」に一度まとめて置き換えたいとき。
- ヒーローセクションに大きめの説明イラストを入れたいとき。
- 特徴カードや説明ブロックに統一感のある SVG / PNG を使いたいとき。
- テキストだけでは弱い LP やサービスサイトに視覚的な補強を入れたいとき。
- アイコン単体よりも、ある程度情報量のあるイラストが欲しいとき。

## Workflow

### Phase 1: 必要な画像を洗い出す
1. ページ内の画像差し替え候補を一覧化する。
2. 各セクションに必要なテーマを短い英語で定義する。
3. 画像の用途を決める。

例:
- `hero_collaboration`
- `feature_automation`
- `empty_state_dashboard`
- `about_remote_work`

用途の分類:
- hero
- feature block
- card illustration
- empty state
- onboarding section

### Phase 2: Themeisle で候補を探す
1. まず Themeisle Illustrations ページを開く。
2. ページ全体から、必要なテーマに近い絵柄を探す。
3. 複数候補がある場合は、1ページ内で混ぜすぎず同系統のタッチに寄せる。
4. 色変更機能がある場合は、サイトの基調色に寄せるか、中立色のまま使う。

### Phase 3: 形式を選んでダウンロードする
1. 原則:
- レスポンシブで綺麗に拡大縮小したいなら `SVG`
- すぐ使いたい、編集不要、表示だけでよいなら `PNG`
2. 保存先を先に決める。

例:
- `{project}/images/`
- `{project}/public/images/illustrations/`

3. ファイル名はプロジェクト内で意味が通る英語名にする。

例:
- `hero-teamwork.svg`
- `feature-automation.svg`
- `empty-dashboard.png`

4. ダウンロードがブラウザ操作前提で自動化しにくい場合は、ユーザーに保存済みファイルまたは直接URLの提供を依頼して続行する。

### Phase 4: Webサイトへ組み込む
1. ヒーローや説明セクションでは、イラスト専用コンテナを置く。
2. 同一グループのカードでは、コンテナ寸法を統一する。
3. SVG はそのまま `img` 参照でもよいが、色や細部調整が必要なら inline SVG も検討する。

```html
<div class="illustration-container">
  <img src="images/hero-teamwork.svg" alt="チームで連携して作業するイメージ">
</div>
```

```css
.illustration-container {
  width: 320px;
  max-width: 100%;
  aspect-ratio: 4 / 3;
  display: flex;
  align-items: center;
  justify-content: center;
}

.illustration-container img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
```

### Phase 5: デザインに合わせて整える
1. イラストの色数が強すぎる場合は、周囲UIの色数を減らしてバランスを取る。
2. 1ページ内に複数イラストを使う場合は、サイズと余白を同じルールにそろえる。
3. ヒーローだけ大きめ、カードは小さめなど、役割ごとのサイズ体系を固定する。

## Quality Rules
- 同じページで複数の絵柄系統を混ぜすぎない。
- `alt` 属性を省略しない。
- 装飾目的だけで使う場合も、意味のある画像なら説明を入れる。
- まず `SVG` を優先検討し、不要な高解像度 PNG を増やしすぎない。
- 画像の見た目を揃えるため、同じカード群ではコンテナサイズを統一する。
- ヒーロー画像だけ極端に大きくしすぎて、本文より目立ちすぎないようにする。
- 商用利用や再配布条件は Themeisle 側の最新利用条件を確認してから使う。

## Coordination
- ページ全体のUIも作る場合は `.agent/skills/web-design/frontend-design/SKILL.md` と組み合わせる。
- 日本語テイストのやわらかい挿絵が欲しい場合は `tyoudoii-illust-fetcher` を候補に含め、ユーザー選択を必ず確認する。

## Verification
1. 1つのWebプロジェクトで Themeisle 素材を 2点以上選ぶ。
2. ダウンロード形式、ファイル保存、HTML組み込みまで完了する。
3. ヒーローまたはカード群で画像サイズが統一されているか確認する。
4. モバイル幅でも画像が潰れず、本文とのバランスが崩れないか確認する。
