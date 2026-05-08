---
name: x-long-article-writer
description: Xの長文記事・長文ポスト・スレッド記事を、アカウント別トンマナに合わせて作成し、Markdownで保存する。セミナー台本、Obsidian保存ノート、既存記事、箇条書きメモをX向けの読み物へ再構成し、ぐうたらAI社長あいと等のアカウント設定とテンプレートを使って後から変更可能な形で出力する。
---

# x-long-article-writer スキル

## 役割

セミナー台本、会話メモ、Obsidianノート、既存記事、箇条書き案をもとに、Xで読まれる長文記事を作る。

短文投稿を量産する `x-post-writer` とは分け、以下に特化する。

- X長文記事
- 長文ポスト
- スレッド化しやすい記事
- note記事へ転用できる下書き
- アカウント別の口調・導線に合わせた再構成

## 保存先

原則:

```text
personal/<account>/outputs/x-long-articles/YYYY-MM-DD/<slug>.md
```

例:

```text
personal/deguchishouma/outputs/x-long-articles/2026-05-08/ai-agent-harness.md
```

ユーザーが保存先を指定した場合はそれを優先する。

## 参照ファイル

- ぐうたらAI社長あいと: `references/accounts/gutara-ai-shacho-aito.md`
- 汎用テンプレート: `assets/templates/x-long-article-template.md`
- 既存X投稿アカウント情報: `.agent/skills/x-post-writer/accounts/gutaraaikatuyou/gutaraAikatuyou.md`

アカウント設定を詳しく調整するときは、まず `references/accounts/` の対象ファイルを読む。

## ワークフロー

1. 入力素材を確認する。
   - セミナー台本
   - 既存Markdown記事
   - Obsidianノート
   - 会話ログ
   - 箇条書きメモ
2. 対象アカウントを決める。
   - 未指定なら `gutara-ai-shacho-aito` を使う。
3. アカウント設定を読む。
4. 記事の目的を決める。
   - 価値提供
   - プロフ流入
   - LINE登録
   - note記事導線
   - 講座・セミナーへの理解促進
5. 参照すべき文脈を集める。
6. 素材をX向けに再構成する。
7. Markdownファイルとして保存する。
8. 必要ならGoogle Driveコピー用コマンドを提示する。実行はユーザーに任せる。

## 参照優先順位

記事作成時は、ユーザーの入力だけで完結させない。以下を見て、主張・トンマナ・実例がズレないようにする。

1. ユーザーが今回言ったこと
2. 対象アカウント設定
3. 既存X投稿アカウント情報
4. Obsidianに保存された関連ノート
5. team-info repo内で実際にやっている仕組み・ファイル構造・スキル
6. 元素材（セミナー台本、記事、メモなど）

特にAI活用・AIエージェント・設定ファイル・Obsidian・Codex/Claude Codeに関する記事では、次を優先的に確認する。

- `personal/<account>/obsidian/claude-obsidian/wiki/index.md`
- `personal/<account>/obsidian/claude-obsidian/wiki/hot.md`
- `personal/<account>/obsidian/claude-obsidian/wiki/sources/`
- `personal/<account>/obsidian/claude-obsidian/wiki/meta/`
- `AGENTS.md`
- `RULES.md`
- `.agent/skills/x-post-writer/accounts/gutaraaikatuyou/gutaraAikatuyou.md`
- `.agent/skills/x-long-article-writer/references/accounts/gutara-ai-shacho-aito.md`

Obsidianノートは「主張の補助」として使う。記事本文では、必要に応じて自然な表現へ変換し、内部パスをそのまま読者に見せすぎない。

## 記事構成

基本はこの順番にする。

### 本文パート

本文パートは人間に向けて書く。読者が最後まで読みたくなるように、価値提供、納得感、具体例を優先する。

1. 強いフック
2. 読者の悩み・誤解
3. 逆張りまたは本質提示
4. 具体例・比喩
5. 手順化
6. 明日やること
7. 自然なCTA

### 最後の実行ブロック

記事の最後に、最後まで読んだ人向けの実用ブロックを置く。

役割は「ここから下をAIエージェントに渡せば、そのままやってくれる」状態にすること。

見出し例:

- `ここから下をAIエージェントに渡せばOK`
- `コピペ用: AIエージェントへの依頼文`
- `実行用プロンプト`

このブロックは本文の補足ではなく、読者への追加価値として扱う。
本文中に長すぎるコマンドやプロンプトを差し込みすぎず、読み物としての流れを守る。

X長文では、見出しを多くしすぎず、1文を短くする。

## 必ず入れる補足要素

AI活用記事では、ただ概念を語るだけで終わらせない。可能な限り以下を入れる。

### AIへの渡し方

読者がそのまま使える形で、「AIにどう渡せばいいか」を書く。

AIエージェント活用の記事では、読者がコピペしてCodex / Claude Code / Gemini CLIなどに渡せば、そのまま作業が始まるレベルまで具体化する。
ただし、これは原則として記事の最後に置く。
本文では人間向けに「なぜそれが大事か」「どう使うと成果につながるか」を説明し、最後に実行用の完成プロンプトをまとめる。

入れる内容:

- 目的
- 前提
- 参照してほしいファイル
- 作ってほしいファイル
- 守ってほしいルール
- セキュリティ注意
- 完了条件

例:

```text
この投稿を参考に、私のアカウント向けにX長文記事を作って。
読者はAI副業初心者。
目的は、プロンプトではなく材料と設定ファイルが大事だと伝えること。
私の過去投稿の口調に合わせて、最後は自然に行動提案して。
```

AIエージェントへ渡す実行プロンプト例:

```text
あなたは私のAI作業アシスタントです。
以下の目的に沿って、作業フォルダ内のファイルを読み、必要なファイルを作成・更新してください。

目的:
- X長文記事を作る
- 私の過去投稿、Obsidianノート、アカウント設定から口調を合わせる
- 初心者でも真似できる手順、コマンド、ファイル構造を入れる

参照してほしいもの:
- AGENTS.md
- account.md
- examples/good-posts.md
- notes/
- obsidian/

作ってほしいもの:
- outputs/x-articles/draft.md
- 次回以降も使える account.md の改善案

守ってほしいルール:
- APIキー、トークン、パスワードは本文に直接書かない
- 必要な認証情報は環境変数で扱う
- コマンド例では `<YOUR_API_KEY>` のようなプレイスホルダーを使う
- 生成した記事には、初心者がコピペできるプロンプトと手順を入れる

完了条件:
- X長文記事の下書きがある
- インストール手順がある
- 環境変数の設定例がある
- 最初にAIへ渡す依頼文がある
```

### プロンプト例

記事内に最低1つは、読者がコピペできるプロンプト例を入れる。

例:

```text
以下の素材を読んで、私専用のAI活用ルールに整理して。

目的:
- X長文記事を作る
- 読者にAI副業の始め方を伝える

渡す素材:
- 過去に伸びた投稿
- 競合の投稿
- 自分の違和感メモ
- セミナー台本

出力してほしいもの:
- 記事の主張
- フック案
- 本文構成
- CTA候補
- 次回から使える設定ファイル
```

### ファイル構造例

AIエージェントや設定ファイルの話をする場合は、実際に真似できるファイル構造を入れる。

例:

```text
my-ai-workspace/
├── AGENTS.md              # AIに守ってほしいルール
├── account.md             # 自分の発信軸・読者・口調
├── examples/
│   ├── good-posts.md      # 良いと思った投稿
│   └── bad-posts.md       # 違和感があった投稿
├── notes/
│   └── voice-memo.md      # 音声入力から整理した思考
└── outputs/
    └── x-articles/        # 生成した長文記事
```

### team-info内の実例

ユーザーがすでにやっている工夫として、文脈に合うものを補足する。

- `AGENTS.md`: AIに守らせるルールの正本
- `.dev-mode`: チーム作業と個人作業の切り替え
- `personal/<account>/`: 個人の出力・設定・Obsidianを分ける
- `.agent/skills/`: AIに仕事を任せるための手順書
- `skill-finder`: スキル索引
- `.codex/prompts/` と `.claude/commands/`: CLIごとの入口
- `personal/<account>/obsidian/claude-obsidian/`: 個人知識を貯めるvault

記事内では、読者向けに「僕はこういう構造でやっている」と噛み砕く。

### 初心者向けの開始手順

AIエージェント、Codex、Claude Code、Obsidian、ターミナル、GitHubなど、未経験者がつまずきやすい話題では、概念だけで終わらせない。

読者が「何を入れて、どこに打って、最初に何を頼むか」まで分かるようにする。

入れる内容:

- 必要なもの
  - PC
  - ターミナル
  - Node.js / Git / Obsidian などの前提ツール
  - Codex / Claude Code / Gemini CLI など対象AIエージェント
- インストールコマンド
  - macOS / Windows で差がある場合は分ける
  - コマンドは必ず公式ドキュメントまたは現在のrepo手順を確認してから載せる
  - 不確かな場合は古いコマンドを断定せず、「公式の最新コマンドを確認」と明記する
- 初回起動手順
  - どのフォルダを開くか
  - どのコマンドを実行するか
  - 何を聞かれたらどう答えるか
- 最初の依頼例
  - AIに渡す最初のプロンプト
  - 期待する出力
  - 保存先

記事内の形:

```text
まずやること:
1. Node.jsを入れる
2. Gitを入れる
3. Obsidianを入れる
4. AIエージェントを入れる
5. 作業フォルダを作る
6. AGENTS.mdにルールを書く
7. 最初のメモをAIに整理してもらう
```

ターミナルコマンドは、読者がそのままコピーできるコードブロックにする。

```bash
# 例: 実際の記事では対象ツールの公式手順を確認して最新コマンドに置き換える
mkdir -p ~/my-ai-workspace
cd ~/my-ai-workspace
```

初心者向け記事では、`cd`、`mkdir`、`npm`、`git` などの意味も一言で補足する。
ただし長くなりすぎる場合は、本文では最小限にして「まずこの順番でやればOK」に寄せる。

### セキュリティと環境変数

repo、API、AIエージェント、GitHub、Google Drive、OpenAI、Anthropic、Discord、Slackなどの話をする場合、APIキーやトークンをファイル本文・記事本文・Git管理下の設定ファイルに直書きする案内はしない。

必要だと思うタイミングでは、環境変数を使う案内と、読者がコピーできるコマンド例を入れる。

原則:

- 実在のAPIキー、トークン、パスワードは出さない
- `<YOUR_API_KEY>`、`<YOUR_TOKEN>`、`<YOUR_WEBHOOK_URL>` のようなプレイスホルダーを使う
- `.env` を使う場合は `.gitignore` に入れる説明を添える
- macOS / Linux は `export` または `.zshrc` / `.bashrc` 例を出す
- Windows PowerShell は `$env:NAME="..."` 例を出す
- 永続設定は便利だが、共有PCでは注意が必要と一言添える

コードブロック例:

```bash
# macOS / Linux: そのターミナルだけで使う場合
export OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
export ANTHROPIC_API_KEY="<YOUR_ANTHROPIC_API_KEY>"
```

```bash
# macOS / Linux: 毎回使えるようにする場合
echo 'export OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"' >> ~/.zshrc
echo 'export ANTHROPIC_API_KEY="<YOUR_ANTHROPIC_API_KEY>"' >> ~/.zshrc
source ~/.zshrc
```

```powershell
# Windows PowerShell: そのターミナルだけで使う場合
$env:OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
$env:ANTHROPIC_API_KEY="<YOUR_ANTHROPIC_API_KEY>"
```

```bash
# .env を使う場合
cat > .env.example <<'EOF'
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_API_KEY>
DISCORD_WEBHOOK_URL=<YOUR_DISCORD_WEBHOOK_URL>
EOF

echo ".env" >> .gitignore
```

記事では、必要に応じて「本物のキーは `<YOUR_API_KEY>` の部分にだけ入れる。SNSやGitHubに貼らない」と噛み砕く。

## ぐうたらAI社長あいと向けの調整

初期設定では以下を守る。

- ぐーたら、怠け者でも成果、AI差別化を軸にする。
- 「努力しろ」ではなく「仕組み化すればラクになる」に寄せる。
- 初心者にも中級者にも刺さるように、専門用語はすぐ噛み砕く。
- 感情より、戦略・仕組み・差別化を前面に出す。
- 口調はカジュアル寄り。ただし長文記事では `ｗ` を使いすぎない。
- noteやLINEへの定型誘導で終わらせない。まず価値提供を完結させる。
- 「フォロワー少なくても」「存在するだけで勝てる」「圧倒的差別化」は文脈が合う時だけ使う。

## 出力ルール

Markdownの先頭に編集用メタ情報を入れる。

```markdown
---
title: "記事タイトル"
account: "gutara-ai-shacho-aito"
source: "元素材パス or brief"
purpose: "価値提供"
status: draft
created: YYYY-MM-DD
---
```

その後に以下を入れる。

- `# タイトル`
- `## 投稿本文`
- `## ファイル構造・活用例`
- `## はじめ方・インストール手順`
- `## セキュリティ・環境変数`
- `## ここから下をAIエージェントに渡せばOK`
- `## AIへの渡し方・プロンプト例`
- `## AIエージェントにそのまま渡す作業依頼`
- `## スレッド分割案`
- `## CTA候補`
- `## 再利用メモ`

## 品質チェック

保存前に確認する。

- 冒頭3行で読む理由があるか。
- 読者の悩みが具体的か。
- アカウントのキャラに合っているか。
- 「難しい」で終わらず「自分にもできそう」に着地しているか。
- CTAが強引すぎないか。
- X上で読みやすいように1文が短いか。
- 既存素材の丸写しではなく、X向けに再構成されているか。
- Obsidian・過去投稿・repo内の実例を確認したか。
- 読者がコピペできるプロンプト例があるか。
- 具体的なファイル構造または運用例があるか。
- 「僕が実際にやっている工夫」として補足できる内容を入れたか。
- AIエージェント未経験者向けに、必要なツール、インストールコマンド、初回起動、最初の依頼例があるか。
- コマンドを載せる場合、最新性が怪しいものを断定していないか。
- AIエージェントへそのまま渡せる実行プロンプトになっているか。
- APIキー、トークン、Webhook URLなどは環境変数とプレイスホルダーで扱っているか。
- セキュリティ上危ない直書きやGit管理下への保存をすすめていないか。
- 人間向け本文とAIエージェント渡し用ブロックが分かれているか。
- AIエージェント渡し用ブロックが、記事の最後まで読んだ人への実用価値になっているか。

## Google Driveコピー

生成物をGoogle Driveへ共有する場合は、ユーザーに次の形式で案内する。エージェントは自動実行しない。

```bash
rclone copy "$TEAM_INFO_ROOT/personal/<account>/outputs/x-long-articles/YYYY-MM-DD/<slug>.md" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/X長文記事/" --progress
```

rclone が未設定の場合は `.agent/skills/common/git-workflow/gdrive-copy/SKILL.md` の初回セットアップ手順を案内する。
