---
description: "X投稿用の図解・画像をGPT Image 2で生成 ＋ ブックマーク内の長文記事URLをネタとして取り込む"
argument-hint: "[DRAFT_ID=\"uuid\" | TOPIC=\"テーマ\" | MODE=\"image|article|both\"]"
---

この prompt / command は `team-info` リポジトリ専用です。
まず `AGENTS.md` を読み、このリポジトリの運用ルールを確認してください。
次に `.agent/skills/x-post-writer/SKILL.md` を読み、スキル全体の構造・DB連携フローを把握してください。

---

# x-image スキル — X投稿コンテンツ自動生成（図解 + 長文記事取り込み）

## このスキルでできること

| モード | 内容 |
|--------|------|
| `image` | 下書きまたはテーマから図解画像をGPT Image 2で生成しDBに保存 |
| `article` | ブックマーク内の長文記事URLを取得してネタとしてNeon DBに保存 |
| `both` | 上記両方を実行（デフォルト） |

---

## 全体フロー

```
[入力] MODE / DRAFT_ID / TOPIC / bookmarks_latest.json
  ↓
Step 0: アカウントを解決する
  → `.agent/skills/x-post-writer/scripts/accounts_config.json` を読む
  → `bookmarks_latest.json` に `account_profile.account_file_path` があれば最優先で使う
  → 例: `GUTARA` は `@gutaraAikatuyou`（表示名: あいと）と同一アカウント
  → 対応するアカウント情報ファイルは `.agent/skills/x-post-writer/accounts/gutaraAikatuyou.md`

━━━━━━━━━━ PART A: 長文記事取り込み ━━━━━━━━━━
Step A-1: bookmarks_latest.json を読み込む
Step A-2: 各ブックマークのテキストからURLを抽出する
Step A-3: URLが長文記事かどうかを判定する（note.com / zenn.dev / qiita.com / medium.com / substack.com 等）
Step A-4: ブラウズ機能で記事URLを取得し、本文を抽出する
Step A-5: 記事の核心（主張・データ・構成）を要約する
Step A-6: 重複チェック後、長文ネタとしてNeon DBの article_sources テーブルに保存する
Step A-7: ネタから長文X投稿の下書きを生成してdraft_manager.pyで保存する

━━━━━━━━━━ PART B: 図解画像生成 ━━━━━━━━━━
Step B-1: `.agent/skills/x-post-writer/accounts/gutaraAikatuyou.md` を読み、`## ビジュアル世界観` を最優先で使う
Step B-2: 投稿内容（draft_id or テーマ）から核心メッセージを1行で抽出する
Step B-3: 画像プロンプトをnanobanana pro形式で設計する（英語）
Step B-4: ユーザーにプロンプトを提示して承認を得る（API料金が発生するため必須）
Step B-5: scripts/generate_image.py でGPT Image 2（gpt-image-1）を呼び出す
Step B-6: 生成画像をoutputs/images/に保存し、draft_manager.py の image 更新手段で draft_parts.image_url に書き込む
Step B-7: プレビューURLをユーザーに提示する
```

---

## PART A 詳細: 長文記事取り込みフロー

### A-2: URL抽出ルール

ブックマークの `text` フィールドから `https://` で始まるURLをすべて抽出する。
t.co 短縮URLはブラウズ時のリダイレクト先を確認して実URLに正規化する。

### A-3: 長文記事の判定基準

以下のいずれかに該当すれば「長文記事」として扱う:
- ドメインが note.com / zenn.dev / qiita.com / medium.com / substack.com / hatena.ne.jp に含まれる
- URLパスが `/articles/` `/posts/` `/entry/` `/n/` を含む
- 取得した本文が1000文字以上ある

短縮URLや一般的なSNSリンク（x.com / twitter.com / instagram.com）はスキップ。

### A-4: 記事取得ルール

- Codex のブラウズ機能で記事URLの本文を取得する
- 本文の最初の5000文字を抽出する（コンテキスト節約）
- paywall（有料記事）でコンテンツが取れない場合はタイトルと冒頭のみで処理する
- 取得に失敗した場合はスキップしてログに残す

### A-5: 要約の観点

以下を必ず含めた要約を作る:
- **主張**: 記事の一番言いたいこと（1〜2文）
- **根拠・データ**: 数字や事例（あれば）
- **構成の型**: どんな流れで展開しているか
- **バズりやすい切り口**: X投稿に使えそうなフック候補を2〜3個

### A-6: Neon DBへの保存

`article_sources` テーブルがなければ以下のSQLで作成する（実行前にユーザー確認）:

```sql
CREATE TABLE IF NOT EXISTS article_sources (
  source_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  account_id UUID REFERENCES accounts(account_id),
  url TEXT NOT NULL,
  title TEXT,
  summary TEXT,
  hook_candidates TEXT,
  raw_excerpt TEXT,
  from_tweet_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

保存前に `url` または `from_tweet_id` の一致で既存行がないか確認し、重複していれば再保存しない。
保存後、`draft_manager.py save` を呼び出して長文下書きをdraftsテーブルにも作成する。
下書きのmemoには `from_article: [記事タイトル]` を入れる。

### A-7: 長文X投稿の生成ルール

- X有料課金ユーザー対応（最大25,000文字）
- アカウントのトンマナ（.agent/skills/x-post-writer/accounts/[account].md）を読んで適用する
- 記事の「型・視点・データ」を借りて自分の言葉で書き直す（コピーしない）
- ツリー形式（`---`区切り）が適切な長さであれば積極的に使う

---

## PART B 詳細: 図解画像生成フロー

### B-1: ビジュアル世界観の読み込み先（優先順）

**第0優先**: `bookmarks_latest.json` の `account_profile.account_file_path` を使う
なければ `.agent/skills/x-post-writer/scripts/accounts_config.json` を読んで、設定IDとアカウントファイル名を解決する
例: `GUTARA` → `gutaraAikatuyou` → `.agent/skills/x-post-writer/accounts/gutaraAikatuyou.md`

**第1優先**: `.agent/skills/x-post-writer/accounts/[x_username].md` の `## ビジュアル世界観` セクション
**第2優先**: 同ファイルの `## トンマナ・口調` / `## 過去の人気投稿例` / フロー図の使い方 から視覚的傾向を読み取る

accounts/*.md に `## ビジュアル世界観` セクションがなければ、
既存のアカウントファイルに **追記を提案する**（新規ファイルは作らない）。

#### accounts/*.md に追記するフォーマット

```markdown
## ビジュアル世界観

### ブランドカラー
- メイン: [色名 / HEX]
- サブ: [色名 / HEX]
- 背景: [色名 / HEX]

### スタイルキーワード（英語プロンプトに使う）
例: minimalist, flat design, dark background, neon accent, infographic

### 図解パターン
例: 矢印フロー図 / 比較表 / ステップ番号付き / アイコン中心

### NGルール
例: 人物の顔写真はNG / 過度な装飾はNG
```

このフォーマットは `.agent/skills/x-post-writer/SKILL.md` の accounts ファイル規約に準拠する。
既存の accounts/*.md のスタイル・見出し階層に合わせて柔軟に調整してよい。

### B-3: プロンプト設計ルール（nanobanana pro形式）

```
[IMAGE PROMPT]
（英語・世界観キーワード必須・構図を明示）

[COPY]
（画像に入れる日本語テキスト）
```

### B-5: generate_image.py の仕様

スクリプトが存在しなければ自動作成する（作成前に存在確認を必ず行う）。

```
入力  : --prompt "英語プロンプト" --output "保存先パス" [--size 1792x1024]
出力  : PNG画像ファイル
モデル: gpt-image-1（OpenAI API）
認証  : OPENAI_API_KEY 環境変数
```

画像生成後は `draft_manager.py` の画像更新サブコマンドが存在するか確認し、
無ければ既存ファイルへのサブコマンド追加で対応する。新規の管理スクリプトは増やさない。

---

## 必要な環境変数

| 変数名 | 用途 |
|--------|------|
| `NEON_DATABASE_URL` | Neon PostgreSQL接続 |
| `X_CONSUMER_KEY` | X API認証 |
| `X_CONSUMER_SECRET` | X API認証 |
| `X_ACCESS_TOKEN_GUTARA` | GUTARAアカウントのトークン |
| `X_ACCESS_TOKEN_SECRET_GUTARA` | GUTARAアカウントのシークレット |
| `DISCORD_WEBHOOK_X_DRAFT` | 下書き保存完了時のDiscord通知 |
| `OPENAI_API_KEY` | GPT Image 2（画像生成）用 |

---

## 実行例

```bash
# ブックマークから記事取り込み＋画像生成を両方やる（デフォルト）
/prompts:x-image

# 記事取り込みのみ
/prompts:x-image MODE="article"

# 指定した下書きの図解画像だけ作る
/prompts:x-image DRAFT_ID="xxxx-yyyy" MODE="image"

# テーマを直接指定して画像生成
/prompts:x-image TOPIC="ブックマークから投稿を自動生成するフロー" MODE="image"
```

---

## 実装チェックリスト（Codexが実行前に確認する）

- [ ] `bookmarks_latest.json` が存在するか（なければ fetch_bookmarks.py の実行を促す）
- [ ] `article_sources` テーブルがNeon DBに存在するか（なければ作成SQLを提示）
- [ ] `accounts_config.json` から `GUTARA` と `gutaraAikatuyou` の対応を解決したか
- [ ] `generate_image.py` が存在するか（なければ作成）
- [ ] `accounts/gutaraAikatuyou.md` に `## ビジュアル世界観` があるか（なければ既存ファイルへの追記を提案）
- [ ] `OPENAI_API_KEY` が設定されているか（画像生成時のみ）
- [ ] 画像生成前にプロンプトをユーザーに提示して承認を得たか

---

## 禁止事項

- 既存の `draft_manager.py` / `preview_server.py` / `fetch_bookmarks.py` の既存ロジックを改ざんしない
- `generate_image.py` を重複作成しない（必ず事前に存在確認）
- ユーザー確認なしにAPIを呼び出さない（画像生成・記事保存ともに）
- `outputs/` 以下のバイナリをgitに追加しない（.gitignore対象）
- 1回の実行で生成する画像は最大3枚まで（API料金節約）
