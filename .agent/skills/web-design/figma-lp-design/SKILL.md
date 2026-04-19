---
name: figma-lp-design
description: DESIGN.md + Figma MCP を使ってLPデザインをFigma上で直接制作する。ブランドスタイルをDESIGN.mdに定義 → Figmaでデザイン → コード生成まで一気通貫で担う。
---

# figma-lp-design スキル

## 役割

**DESIGN.md**（Google Stitch が導入した「プレーンテキストのデザインシステム文書」）と **Figma MCP** を組み合わせ、LPデザインを Figma 上で直接制作する。

```
DESIGN.md（デザイン仕様書）
    ↓ AIが読んで一貫したUIを生成
Figma（デザイン制作・確認）
    ↓ エクスポート
コード実装（frontend-design スキルへ引き渡し）
```

---

## DESIGN.mdとは

`AGENTS.md` がコーディングエージェント向けの行動指針であるように、`DESIGN.md` はデザインエージェント向けの視覚仕様書。

| ファイル | 誰が読む | 何を定義する |
|---------|---------|------------|
| `AGENTS.md` | コーディングエージェント | プロジェクトの作り方 |
| `DESIGN.md` | デザインエージェント | プロジェクトの見た目と質感 |

- JSON スキーマ不要・Figmaエクスポート不要
- Markdownだけ → LLMが最も得意な形式
- プロジェクトルートに置くだけで、どの AI エージェントも即座に理解する

**参照リソース：** [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) — 66社のブランドをベースにした DESIGN.md テンプレート集

---

## 前提条件

- Figma MCP が認証済みであること（`mcp__figma__*` ツール群が使用可能な状態）
- 認証されていない場合は `/mcp` コマンドで figma を選択して認証を完了させること

---

## ワークフロー

### Step 0：DESIGN.md の選定・作成（★新規追加）

LP制作を始める前に必ず DESIGN.md を用意する。これが以降のすべてのデザイン判断の基準になる。

#### オプション A：テンプレートから選ぶ（推奨）

以下のカテゴリから、ブランドトーンに近いテンプレートを選ぶ。

| ブランドトーン | おすすめテンプレート | 特徴 |
|-------------|-------------------|------|
| 信頼感・プロフェッショナル | `stripe` / `linear` | パープル系・ミニマル |
| クリーン・ノートPC系 | `notion` / `vercel` | ウォームミニマル / 白黒精密 |
| フレンドリー・親しみやすい | `intercom` / `zapier` | ブルー系 / オレンジ系 |
| 高級感・プレミアム | `apple` / `ferrari` | 上品な余白・写真重視 |
| テック・スタートアップ | `cursor` / `supabase` | ダーク系・グラデーション |
| シンプル・教育系 | `cal` / `mintlify` | ニュートラル・読みやすさ重視 |

インストールコマンド（ユーザーが実行）：
```bash
cd "$TEAM_INFO_ROOT/outputs/lp-design/[プロジェクト名]" && npx getdesign@latest add [テンプレート名]
# 例: npx getdesign@latest add stripe
```

#### オプション B：DESIGN.md をゼロから作る

ユーザーの要件をヒアリングし、以下のテンプレートに沿って生成する。

```markdown
# Design System — [プロジェクト名]

## 1. Visual Theme & Atmosphere
[デザインの雰囲気・哲学を1〜2段落で記述]

## 2. Color Palette & Roles
- **Primary** (`#XXXXXX`): CTAボタン・リンク・強調色
- **Background** (`#FFFFFF`): ページ背景
- **Surface** (`#XXXXXX`): カード・セクション背景
- **Heading** (`#XXXXXX`): 見出しテキスト
- **Body** (`#XXXXXX`): 本文テキスト
- **Accent** (`#XXXXXX`): バッジ・装飾要素
- **Border** (`#XXXXXX`): 線・区切り

## 3. Typography Rules
| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| Hero | [フォント] | 40px | 700 | 1.15 | -0.5px |
| H2 | [フォント] | 28px | 600 | 1.3 | normal |
| H3 | [フォント] | 20px | 600 | 1.4 | normal |
| Body | [フォント] | 16px | 400 | 1.7 | normal |
| Caption | [フォント] | 13px | 400 | 1.5 | normal |

## 4. Component Stylings
### Buttons
- Primary: [背景色] bg, white text, [radius]px radius, [padding]
- Secondary: transparent bg, [テキスト色] text, 1px solid border
### Cards
- Background: white, 1px solid [border色], [radius]px radius
- Shadow: [shadow定義]

## 5. Layout Principles
- Max width: [幅]px（スマホ最適化LPは390px基準）
- Padding (mobile): 24px
- Section gap: 64px
- 8pt グリッド（8の倍数でスペーシング）

## 6. Depth & Elevation
[shadow定義]

## 7. Do's and Don'ts
### Do
- [守るべきルール]
### Don't
- [避けるべきパターン]

## 8. Responsive Behavior
- Mobile: 390px（基準）
- Tablet: 768px
- Desktop: 1280px（縦長LP維持）

## 9. Agent Prompt Guide
### Quick Color Reference
- CTA: [Primary色]
- Background: [背景色]
- Heading: [見出し色]
- Body: [本文色]
### Example Prompts
- "[Hero セクションの生成プロンプト例]"
```

#### オプション C：既存の DESIGN.md を流用・カスタマイズ

テンプレートをベースに色やフォントだけを変更する場合。ファイルを直接 Edit して調整する。

---

### Step 1：ヒアリング

以下の項目をユーザーに確認する。

| 項目 | 質問例 |
|------|--------|
| サービス・商品名 | 何を売る / 伝えるLPですか？ |
| ターゲット | 誰に向けたLPですか？ |
| ゴール | CV（申し込み / 購入 / 登録）は何ですか？ |
| トーン | ブランドカラー・雰囲気（クール / 温かみ / 高級 など） |
| 参考URL | 好きなデザインや競合サイトがあれば教えてください |
| 既存Figmaファイル | 既存ファイルに追加するか、新規作成か |
| DESIGN.md | テンプレート希望（A）/ ゼロから（B）/ 既存流用（C）|

---

### Step 2：LP構成設計

ヒアリング結果をもとに、LPのセクション構成を提案する。  
**DESIGN.md の `Agent Prompt Guide` セクションを参照しながら**、各セクションの仕様を具体化する。

**基本構成テンプレート（Webサービス・SaaS向け）**

```
1. Hero（キャッチコピー + CTA）          ← DESIGN.md の Hero プロンプトを使用
2. 課題提起（ターゲットの悩み）
3. 解決策の提示（サービス概要）
4. 特徴・機能一覧（3〜4項目）            ← DESIGN.md のカード定義を使用
5. ソーシャルプルーフ（実績・お客様の声）
6. 料金プラン（あれば）
7. FAQ
8. 最終CTA（申し込みボタン）
9. フッター
```

ユーザーの要件に合わせてセクションを増減し、確認を取ってから次に進む。

---

### Step 3：Figmaファイル準備

Figma MCP（`mcp__figma__*`）を使ってFigmaファイルを準備する。

#### 新規作成の場合

**推奨フレーム構成：**
- `LP_Mobile`：幅 390px（スマホ最適化LPの基準）
- `LP_Desktop_Narrow`：幅 800px（PC表示でも縦長を維持する設定）
- `Components`：再利用パーツ置き場
- `Design_Tokens`：DESIGN.md から抽出したカラー・タイポグラフィ定義

#### 既存ファイルに追加する場合

ユーザーからFigmaファイルのURLを受け取り、既存構造を確認してから作業する。

---

### Step 4：デザイントークンの Figma への反映

**DESIGN.md の Section 2（Color）と Section 3（Typography）をそのまま Figma に転記する。**

Figmaでのトークン定義方法：
1. カラースタイルとして登録（右パネル → Style → ＋）
2. テキストスタイルとして登録（同様）
3. DESIGN.md の「Role」名をそのままスタイル名に使う

---

### Step 5：セクション別デザイン実装

**DESIGN.md の Section 9（Agent Prompt Guide）の「Example Component Prompts」を各セクションに対応させながら制作する。**

各セクションを制作するとき、次のプロンプトをベースに DESIGN.md の値を当てはめて Figma で指示する：

#### Hero セクション
DESIGN.md の Hero プロンプト例をそのまま使い、コピーを差し替える。

- キャッチコピー：`heading-xl` サイズ・DESIGN.md 指定 weight
- サブコピー：`body-lg` サイズ・DESIGN.md 指定 weight
- CTA ボタン：DESIGN.md の Primary Button 仕様
- セカンダリテキスト：登録3分 · 売り込みなし

#### 特徴カードセクション
DESIGN.md のカード定義（背景・ボーダー・シャドウ・ラジウス）を適用。

- アイコン + 見出し + 説明のカード
- DESIGN.md の Section 4（Component Stylings / Cards）を使用

#### 比較・CTAセクション
DESIGN.md の dark section 定義があれば使用。なければ Primary カラーで強調背景を作る。

---

### Step 6：レスポンシブ対応

**DESIGN.md の Section 8（Responsive Behavior）の Collapsing Strategy を適用する。**

- Mobile（390px）を先に完成させる → LP の実態に合わせた基準
- Desktop Narrow（800px）でも縦長を維持し、max-width: 600px 程度で中央揃え
- DESIGN.md の各ブレイクポイントごとの変更をそのまま Figma で再現

---

### Step 7：DESIGN.md の最終更新

LP 制作中に生まれた固有のデザイン判断を DESIGN.md に追記する。

追記すべき内容の例：
- LP専用のカラー（例：緊急性を示すアクセントカラー）
- LP専用コンポーネント（バッジ、タイムライン、比較表など）
- このLP特有の「Don't」

---

### Step 8：アセットエクスポート

Figmaから開発実装用にアセットをエクスポートする。

**エクスポート対象**
- ロゴ・アイコン：SVG
- イラスト・画像：PNG（2x）/ WebP
- デザインスペック：Figmaの「開発モード」で共有URLを発行
- **DESIGN.md**：コード実装エージェントへ渡すメイン仕様書

**出力先（ユーザーが実行）**
```bash
mkdir -p "$TEAM_INFO_ROOT/outputs/lp-design/[プロジェクト名]/assets"
# DESIGN.md を出力フォルダにもコピーしておく
cp "$TEAM_INFO_ROOT/outputs/lp-design/[プロジェクト名]/DESIGN.md" \
   "$TEAM_INFO_ROOT/outputs/lp-design/[プロジェクト名]/assets/"
```

Google Drive へのコピー：
```bash
rclone copy "$TEAM_INFO_ROOT/outputs/lp-design/[プロジェクト名]/" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/lp-design/[プロジェクト名]/" --progress
```
※ rclone 未設定の場合は `.agent/skills/common/git-workflow/gdrive-copy/SKILL.md` を参照。

---

## 品質チェックリスト

制作完了前に以下を確認する。

### DESIGN.md
- [ ] DESIGN.md がプロジェクトフォルダに存在するか
- [ ] カラー・タイポグラフィ・コンポーネント定義が揃っているか
- [ ] Agent Prompt Guide セクションに Example Prompts があるか

### デザイン
- [ ] キャッチコピーがターゲットの課題に刺さる内容か
- [ ] CTAボタンが目立つ位置に配置されているか（Hero + 最終CTA 最低2箇所）
- [ ] コントラスト比が 4.5:1 以上か（テキストと背景）
- [ ] フォントサイズが本文16px以上か
- [ ] モバイル（390px）フレームが完成しているか
- [ ] デザイントークンが DESIGN.md と Figma スタイルで一致しているか
- [ ] コンポーネント化されたパーツが再利用可能な状態か

---

## コード実装への引き渡し

Figma でのデザインが完了したら、DESIGN.md をコード実装エージェントに渡す。

```
DESIGN.md を渡したうえで:
「このDESIGN.mdのデザインシステムに従って、
 添付のLP構成でHTMLとTailwind CSSでコーディングしてください。
 スマホ最適化（390px基準）・PCでも縦長を維持してください。」
```

→ `frontend-design` スキル または `gsap-awwwards-website` スキルへ引き渡す。

---

## 連携スキル

| スキル | 用途 |
|--------|------|
| `frontend-design` | DESIGN.md + LP構成をHTML/CSSに実装する |
| `gsap-awwwards-website` | スクロールアニメーション付きLPを実装する |
| `themeisle-illustration-fetcher` | LP用のイラスト素材を取得する |
| `tyoudoii-illust-fetcher` | 日本語テイストのイラストを取得する |
| `clone-website` | 参考サイトをNext.jsで複製する |

---

## 参照リンク

- [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) — 66社のDESIGN.mdテンプレート集
- [getdesign.md](https://getdesign.md) — ブラウザでプレビュー・CLIでインストール
- [Google Stitch DESIGN.md 仕様](https://stitch.withgoogle.com/docs/design-md/format/) — 公式フォーマット定義
