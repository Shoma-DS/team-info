---
name: tyoudoii-illust-fetcher
description: Search and download free illustrations from tyoudoii-illust.com via WordPress REST API, then integrate them into web projects with uniform CSS sizing. Use when building web pages that need Japanese-style free illustrations instead of emoji or placeholder icons.
---

# Tyoudoii Illust Fetcher Skill

## Goal
- Use the tyoudoii-illust WordPress REST API when the site itself is hard to scrape because of JS rendering.
- Replace emoji, text icons, or placeholder art with downloadable illustrations that fit the page design.
- Pair this skill with `.agent/skills/web-design/frontend-design/SKILL.md` when the surrounding layout or card UI also needs cleanup.

## Workflow

### Phase 1: 必要なイラストを洗い出す
1. HTML / JSX / component 内の絵文字、テキストアイコン、仮画像を一覧化する。
2. 各箇所に必要なイラストのテーマをキーワード化する。
3. キーワードはまず意味が通る短語で置く。
4. ダウンロード先ディレクトリを先に決める。

例:
- `worry_man`
- `robot`
- `handshake`
- `{project}/images/`
- `{project}/public/images/`

### Phase 2: WordPress REST APIで検索
1. まず REST API を使って候補投稿を探す。
2. エンドポイント:

```text
https://tyoudoii-illust.com/wp-json/wp/v2/posts?search={keyword}&_embed=true&per_page=5
```

3. レスポンスの `_embedded["wp:featuredmedia"][0].source_url` からサムネイルURLを取る。
4. サムネイルURLが取れない場合は、日本語キーワードと英語キーワードを切り替えて再検索する。

サムネイルURL例:

```text
https://tyoudoii-illust.com/wp-content/uploads/2024/01/example_サムネ.png
```

### Phase 3: 実際のイラストURLを導出
1. サムネイルURL末尾の `_サムネ.png` を `_color.png` に置換して本命URLを作る。
2. まず HTTP 200 になるかを確認する。

```bash
curl -s -o /dev/null -w "%{http_code}" "{candidate_url}"
```

3. `_color.png` が 404 の場合は次を順に試す。
- `_カラー.png`
- `_illust.png`
4. どれも 200 にならなければ、別キーワードで API 検索に戻る。

### Phase 4: ダウンロード
1. プロジェクト内で意味が通る英語ファイル名にする。
2. 例:
- `telework.png`
- `robot.png`
- `support.png`
3. ダウンロード例:

```bash
curl -L "{url}" -o "{project}/images/{semantic_name}.png"
```

### Phase 5: HTMLとCSSへの組み込み
1. 絵文字やテキストアイコンをローカル画像へ置き換える。

```html
<div class="icon-container">
  <img src="images/{name}.png" alt="{説明}">
</div>
```

2. カードや特徴一覧では、全アイコンに同じコンテナサイズを使う。
3. 画像自体の縦横比は `object-fit: contain` で吸収する。

```css
.icon-container {
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-container img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
```

## Quality Rules
- WebFetch やレンダリング済みHTMLの取得に固執せず、まず REST API を使う。
- サムネURLが取れなかった場合は、日本語/英語の類義語で再試行する。
- `_color.png` が 404 の場合は `_カラー.png` と `_illust.png` も確認する。
- 同じカード群でアイコンコンテナサイズを混在させない。
- `alt` 属性は省略しない。
- 保存ファイル名はプロジェクト内で意味が通る英語名にする。
- 商用利用時は tyoudoii-illust.com の最新利用規約を必ず確認する。無料・商用可の前提で進めても、最終確認は省略しない。

## Coordination
- `themeisle-illustration-fetcher` も候補に入る場合は、自動で選ばず必ずユーザーにどちらを使うか確認する。
- UI全体の改修やセクション設計も必要なら `frontend-design` を先に読み、アイコン差し替え工程だけこのスキルで処理する。
- 既存デザインがある場合は、その余白・カード比率・画像サイズ方針に合わせて `.icon-container` の寸法だけ調整する。

## Verification
1. 新規Webプロジェクトでこのスキルを呼び出し、キーワードから API 検索を開始する。
2. 候補URLの 200 確認、PNG ダウンロード、HTML 組み込みまで一通り完了することを確認する。
3. ブラウザで全カード画像が同一サイズに揃って見えるか目視確認する。
