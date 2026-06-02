---
name: x-long-article-draft-saver
description: X長文記事作成の統合正本。Loom MCP の文字起こし、セミナー台本、Obsidianノート、既存記事、repo実例、アプリ画面、Xアカウント設定を参照し、専門用語を残しつつ寄り添い・言い換え・例え話で噛み砕いた記事構成・Markdown本文・5:2ヘッダー画像・本文内画像・article_plain.txt・Kimi WebBridgeでのX Articles下書き保存まで一気通貫で扱う。本文だけ作る場合もこのスキルを使い、下書き保存工程だけをスキップする。
---

# x-long-article-draft-saver スキル（X長文記事 統合版）

## 役割

X長文記事作成の正本スキルとして、素材収集、構成、本文執筆、画像設計、X下書き保存までを扱う。

本文だけを作る場合もこのスキルを読み、Kimi WebBridgeによるX下書き保存工程だけをスキップする。

対象にする素材:

- Loom MCP の録画文字起こし、summary、chapters
- セミナー台本、会話メモ、箇条書き案
- Obsidianノート、既存Markdown記事、過去記事
- Desktop上の実repo、アプリ、ファイル構造
- アプリのスクリーンショット、管理画面、ログ画面
- 対象Xアカウント設定、過去投稿、競合・見本投稿

作るもの:

- 5:2 のヘッダー画像
- X長文記事本文
- X Articles へ貼り付けるプレーンテキスト
- Kimi WebBridge による X 下書き保存
- `article.md` のMarkdown画像位置に基づく、ヘッダー以外の画像挿入
- スクリーンショット素材を本文へ自然に組み込む配置案
- 保存ログと Google Drive コピー案内

X Articles のヘッダー入力と本文メディア入力はUI上で近く、誤って本文画像がヘッダー/サムネイル候補になる事故が起きやすい。本文内画像はXの `Add Media` やファイル入力ではなく、本文エディタへ画像ファイルを貼り付ける経路を使う。

## 事前確認

新規ファイル・フォルダを作る前に `.dev-mode` を読み、現在モードをユーザーへ提示する。

```text
現在のモード: チーム開発モード
このまま続けてよいですか？
```

`.dev-mode` が `personal` の場合は `personal/<account>/` 配下に出力する。`<account>` は `git config user.name` を小文字化し、空白・記号を除いた名前にする。

## 入力

| 項目 | 必須 | 説明 |
|------|------|------|
| テーマ | ◎ | 例: AIセミナー第1回の内容をX長文記事化 |
| Loom動画IDまたは探す条件 | △ | 未指定なら Loom MCP の `list_videos` で候補を探す |
| 参照したいrepo内台本 | △ | 未指定なら `rg` で候補を探す |
| 対象Xアカウント | △ | 未指定なら `gutara-ai-shacho-aito` |
| CTA | △ | 未指定ならテーマに合わせて自然に作る |
| 下書き保存まで行うか | △ | Xへ送信する前に必ず確認する |

## 出力先

原則:

```text
personal/<account>/outputs/x-long-article-drafts/YYYY-MM-DD/<slug>/
```

作るファイル:

| ファイル名 | 内容 |
|-----------|------|
| `sources.md` | Loom・repo内台本・Obsidian等から拾った要点 |
| `article.md` | Markdown版のX長文記事 |
| `article_plain.txt` | X Articles へ貼るプレーンテキスト |
| `header_prompt.md` | 5:2ヘッダー画像生成プロンプト |
| `header.*` | 生成できた場合のヘッダー画像 |
| `draft-save-log.md` | Kimi WebBridgeでの下書き保存結果、URL、未完了事項 |

同じテーマで再実行するときは上書きせず、slug またはファイル名へ `v2` `v3` を付ける。

## 参照ファイル

- ぐうたらAI社長あいと: `.agent/skills/x-long-article-draft-saver/references/accounts/gutara-ai-shacho-aito.md`
- 汎用テンプレート: `.agent/skills/x-long-article-draft-saver/assets/templates/x-long-article-template.md`
- 既存X投稿アカウント情報: `.agent/skills/x-post-writer/accounts/gutaraaikatuyou/gutaraAikatuyou.md`
- 共有Obsidian: `/Users/deguchishouma/Obsidian/agent-vault/wiki/hot.md`
- repo正本ルール: `AGENTS.md`, `RULES.md`

## 参照優先順位

記事作成時は、ユーザーの入力だけで完結させない。主張・トンマナ・実例がズレないように、次の順で確認する。

1. ユーザーが今回指定したテーマ・CTA・禁止事項
2. Loom MCP で取得した文字起こし、summary、key takeaways
3. repo 内のセミナー台本・スライド構成・LINE導線
4. 対象Xアカウント設定、既存X投稿アカウント情報
5. Obsidianに保存された関連ノート
6. team-info repo内で実際にやっている仕組み・ファイル構造・スキル
7. Desktop上の実repoと起動確認したアプリ画面
8. 既存記事、過去の長文記事、ユーザーの会話メモ

内部パスや作業用語は読者にそのまま見せすぎない。記事内では「実際にセミナーで話したこと」「裏側でやっていること」として自然に翻訳する。

AI活用・AIエージェント・設定ファイル・Obsidian・Codex/Claude Codeに関する記事では、次も優先的に確認する。

- `/Users/deguchishouma/Obsidian/agent-vault/wiki/hot.md`
- `/Users/deguchishouma/Obsidian/agent-vault/wiki/index.md`
- `personal/<account>/obsidian/claude-obsidian/wiki/index.md`
- `personal/<account>/obsidian/claude-obsidian/wiki/hot.md`
- `personal/<account>/obsidian/claude-obsidian/wiki/sources/`
- `personal/<account>/obsidian/claude-obsidian/wiki/meta/`
- `.agent/skills/x-post-writer/accounts/gutaraaikatuyou/gutaraAikatuyou.md`
- `.agent/skills/x-long-article-draft-saver/references/accounts/gutara-ai-shacho-aito.md`

Obsidianノートは「主張の補助」として使う。記事本文では、必要に応じて自然な表現へ変換し、内部パスをそのまま読者に見せすぎない。

## Loom MCP の使い方

Loom動画IDが分かる場合:

1. `mcp__loom__get_video_details` を使う
2. `save_dir` に出力先フォルダの `loom/` を指定する
3. transcript、summary、chapters、comments を確認する

動画IDが不明な場合:

1. `mcp__loom__list_videos` で直近候補を出す
2. タイトル・日付・「AIセミナー」「1回目」「第1回」「AirthMate」などで候補を絞る
3. 複数候補が残る場合はユーザーへ確認する
4. 確定後に `mcp__loom__get_video_details` を使う

文字起こしが取れない場合は、Loom summary と repo 内台本で不足を補う。ただし、録画で話していない実績・数字・約束を捏造しない。

## repo内台本の探し方

ユーザーがパスを指定していない場合は、まず `rg` で候補を探す。

```bash
rg -n -i "AIセミナー|セミナー|1回目|第1回|第一回|2回目|第2回|公式LINE|アーカイブ|AirthMate" "$TEAM_INFO_ROOT" --glob '*.md' --glob '*.txt'
```

候補になりやすい場所:

- `personal/<account>/projects/`
- `personal/<account>/outputs/`
- `.agent/skills/personal/<account>/seminar-script-creator/`
- `.agent/skills/x-long-article-draft-saver/`
- `.agent/skills/x-post-writer/accounts/`

秘密情報、顧客情報、個人名が混ざる場合は、記事では伏せるか一般化する。

## AIセミナー記事の既定方針

今回のAIセミナー記事では、第1回の内容を価値提供として書く。第2回は最後まで読んだ人への限定導線として扱う。

CTA の既定文:

```text
最後まで読んでくれた方限定で、2回目のセミナーアーカイブをお渡ししています。
欲しい方は公式LINEに「2回目」とだけ送ってください。
```

CTA は本文の流れを壊さない位置に置く。売り込みを強くしすぎず、「もっと具体例を見たい人向け」の自然な案内にする。

## 記事構成

X Articles向けに次の順番で作る。

1. タイトル
2. 冒頭フック
3. 第1回セミナーで伝えた結論
4. 読者の誤解・つまずき
5. Loom文字起こしから拾った具体例
6. repo内台本から拾った手順・比喩・実演
7. 今日から真似できる実践ステップ
8. 第2回アーカイブへの限定CTA

記事本文では、見出しを増やしすぎず、1文を短くする。Markdown版では見出しを使ってよいが、`article_plain.txt` ではXのエディタに貼って崩れにくいプレーンテキストへ整える。

### 本文パート

本文パートは人間に向けて書く。読者が最後まで読みたくなるように、価値提供、納得感、具体例を優先する。

基本の流れ:

1. 強いフック
2. 読者の悩み・誤解
3. 逆張りまたは本質提示
4. 具体例・比喩
5. 手順化
6. 明日やること
7. 自然なCTA

専門用語は消しすぎない。読者が検索・学習できるように用語自体は残し、直後に「この言葉だけ聞くと難しく見えるけど、簡単にいうと」の温度で噛み砕く。記事内にrepoパスやコマンドを出す場合は、読者が真似できる範囲に翻訳する。

### 専門用語の噛み砕き方

ただ平易な言葉に置き換えるだけにしない。用語を消すと読者の学びが残らないため、次の型で説明する。

1. 専門用語を出す
2. 「聞き慣れないと分かりにくいと思う」と寄り添う
3. 「要は」「簡単にいうと」で言い換える
4. 身近な例え話か具体例を足す

使いやすい言い換え例:

- プロンプト: AIへの指示文
- AIエージェント: 資料を読んで作業まで進めるAI
- ファイル構造: 資料をどの棚に置くかの決め方
- runtime: 作業中の一時置き場
- schema: 記入用紙の型
- フック: 読者の足を止める冒頭
- メトリクス: 反応を見る数字
- ダッシュボード: 車の運転席のように状態をまとめて見る画面
- ローテーション: 順番に回す仕組み
- セクション: ページ内のひとまとまり
- リンク領域: 画像やページ内でクリックできる場所
- 操作レイヤー: 人間が触って操作する画面
- コンテキストエンジニアリング: AIに渡す前提知識を整えること
- ハーネスエンジニアリング: AIが作業しやすい道具や作業場を整えること

表現例:

```text
AIエージェントという言葉を聞くと、急にエンジニア向けに見えるかもしれない。
でも簡単にいうと、資料を読ませたうえで「ここまで作って」と任せられるAIのこと。
新人にマニュアルと過去資料を渡して、実作業までお願いする感覚に近い。
```

### 最後の実行ブロック

記事の最後に、最後まで読んだ人向けの実用ブロックを置く。

役割は「ここから下をAIエージェントに渡せば、そのままやってくれる」状態にすること。

見出し例:

- `ここから下をAIエージェントに渡せばOK`
- `コピペ用: AIエージェントへの依頼文`
- `実行用プロンプト`

このブロックは本文の補足ではなく、読者への追加価値として扱う。本文中に長すぎるコマンドやプロンプトを差し込みすぎず、読み物としての流れを守る。

## 必ず入れる補足要素

AI活用記事では、ただ概念を語るだけで終わらせない。可能な限り以下を入れる。

- AIへの渡し方
- 読者がコピペできるプロンプト例
- 実際に真似できるファイル構造
- team-info内の実例
- 初心者向けの開始手順
- セキュリティと環境変数の扱い

### AIへの渡し方

AIエージェント活用の記事では、読者がコピペしてCodex / Claude Code / Gemini CLIなどに渡せば、そのまま作業が始まるレベルまで具体化する。

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

### ファイル構造例

AIエージェントや設定ファイルの話をする場合は、実際に真似できるファイル構造を入れる。

例:

```text
my-ai-workspace/
|-- AGENTS.md              # AIに守ってほしいルール
|-- account.md             # 自分の発信軸・読者・口調
|-- examples/
|   |-- good-posts.md      # 良いと思った投稿
|   `-- bad-posts.md       # 違和感があった投稿
|-- notes/
|   `-- voice-memo.md      # 音声入力から整理した思考
`-- outputs/
    `-- x-articles/        # 生成した長文記事
```

### team-info内の実例

ユーザーがすでにやっている工夫として、文脈に合うものを補足する。

- `AGENTS.md`: AIに守らせるルールの正本
- `.dev-mode`: チーム作業と個人作業の切り替え
- `personal/<account>/`: 個人の出力・設定・Obsidianを分ける
- `.agent/skills/`: AIに仕事を任せるための手順書
- `skill-finder`: スキル索引
- `.codex/prompts/` と `.claude/commands/`: CLIごとの入口
- `/Users/deguchishouma/Obsidian/agent-vault`: 共有Obsidian知識ベース

記事内では、読者向けに「僕はこういう構造でやっている」と噛み砕く。

### アプリ構造・スクリーンショットの扱い

ユーザーが作ったアプリを扱う記事では、機能紹介だけで終わらせない。読者が「何のためのアプリで、どんな画面があり、何ができて、どこが便利なのか」まで分かるように書く。

必ず確認して入れる観点:

- 何を解決するアプリか
- 画面構成: ダッシュボード、一覧、編集、画像、ログ、設定など
- できること: 作成、確認、修正、画像生成、ローテーション、同期、下書き保存など
- 裏側の仕組み: データの流れ、保存先、ログ、失敗時の確認方法
- 人間の作業がどこまで減るか
- それでも人間が確認すべき場所

ジモティー関連アプリを扱う場合は、一般読者にも分かるように次を噛み砕く。

- 投稿管理: どの商品・地域・文面を出すかをまとめて見る場所
- 地域ローテーション: 同じ地域に偏らないよう順番に回す仕組み
- 画像管理: 投稿ごとの画像を作り、差し替え、確認する場所
- ログ: いつ何を作ったか、どこで止まったかを見る記録
- Google Drive / シート連携: 作った素材や管理表を後から探せるように置く仕組み

スクリーンショットは記事末尾にまとめて置かない。説明している段落の直後に入れ、画像の前後で「この画面では何を見るのか」を一言添える。あとで素材が入る場合は、`article.md` にMarkdown画像の仮置きを作り、alt textには画面名と読者に見てほしいポイントを書く。

例:

```markdown
ここがジモティー投稿管理のダッシュボード。
ダッシュボードと言われても分かりにくいと思うけど、要は車の運転席みたいに、今の状態を一画面で見る場所です。

![ジモティー投稿管理ダッシュボード。投稿数、地域、状態をまとめて確認できる画面](assets/screenshots/jmty-dashboard-redacted.jpg)
```

個人情報、顧客情報、未公開URL、APIキー、管理IDが写るスクリーンショットは、必ず伏せ字版を使う。

### 初心者向けの開始手順

AIエージェント、Codex、Claude Code、Obsidian、ターミナル、GitHubなど、未経験者がつまずきやすい話題では、概念だけで終わらせない。

読者が「何を入れて、どこに打って、最初に何を頼むか」まで分かるようにする。

ただし、インストールコマンドは最新性が変わりやすい。必要な場合は公式ドキュメントまたは現在のrepo手順を確認してから載せる。不確かな場合は古いコマンドを断定せず、「公式の最新コマンドを確認」と明記する。

### セキュリティと環境変数

repo、API、AIエージェント、GitHub、Google Drive、OpenAI、Anthropic、Discord、Slackなどの話をする場合、APIキーやトークンをファイル本文・記事本文・Git管理下の設定ファイルに直書きする案内はしない。

原則:

- 実在のAPIキー、トークン、パスワードは出さない
- `<YOUR_API_KEY>`、`<YOUR_TOKEN>`、`<YOUR_WEBHOOK_URL>` のようなプレイスホルダーを使う
- `.env` を使う場合は `.gitignore` に入れる説明を添える
- macOS / Linux は `export` または `.zshrc` / `.bashrc` 例を出す
- Windows PowerShell は `$env:NAME="..."` 例を出す
- 永続設定は便利だが、共有PCでは注意が必要と一言添える

## アカウント別トンマナ

対象アカウントが未指定なら `gutara-ai-shacho-aito` を使う。

初期設定では以下を守る。

- ぐーたら、怠け者でも成果、AI差別化を軸にする。
- 「努力しろ」ではなく「仕組み化すればラクになる」に寄せる。
- 初心者にも中級者にも刺さるように、専門用語は残しつつ、直後に寄り添い・簡単な言い換え・例え話で噛み砕く。
- 感情より、戦略・仕組み・差別化を前面に出す。
- 口調はカジュアル寄り。ただし長文記事では `ｗ` を使いすぎない。
- noteやLINEへの定型誘導で終わらせない。まず価値提供を完結させる。
- 「フォロワー少なくても」「存在するだけで勝てる」「圧倒的差別化」は文脈が合う時だけ使う。

## 出力ルール

本文だけ作る場合も、下書き保存まで行う場合も、原則として次を保存する。

- `sources.md`
- `article.md`
- `article_plain.txt`
- `x-draft-assets.md`（画像がある場合）
- `header_prompt.md`（ヘッダー画像を作る場合）
- `draft-save-log.md`（X下書き保存を行う場合、または未実行理由を残す場合）

## ブラウザ本文とMarkdownの同期

既存のX下書きを修正する場合、ブラウザ上の下書き本文を正本にする。

1. Kimi WebBridgeでX Articles編集画面を開く。
2. タイトル入力と本文エディタの `innerText` を抽出する。
3. 抽出したタイトルと本文で `article_plain.txt` を上書きする。
4. 同じ本文から `article.md` を再生成し、Markdown見出しを復元する。
5. 本文内画像を入れたい場所は、`article.md` の対象見出し直下にMarkdown画像として書く。

例:

```markdown
## 「プロンプト力」だけじゃ、もう足りない

![AI活用は3世代で進化した](diagrams/diagram-01-three-generations.png)
```

`article.md` の画像順と見出し位置を、ブラウザ挿入の正本として扱う。図解、感想スクショ、実績スクショ、補足画像など、ヘッダー以外の画像はすべてMarkdown画像として `article.md` に置き場所を書いてからブラウザへ反映する。`x-draft-assets.md` がある場合は、見出し名と画像パスが `article.md` と一致しているか確認する。

ファイル構造やASCIIアートは、必ずMarkdownのコードフェンスに入れる。X Articles のDraft.js内部では `code-block` が一時的に使えても、プレビュー/保存時に通常本文へ戻ることがあるため、読者に確実にコードブロックとして見せたい場合は ` ```text ` と ` ``` ` を本文に残して、その中にツリー構造を書く。

## 本文リズムとXブロック構造

X Articles の本文は、空行だけで間隔を調整しない。`article.md` を構造の正本として、XのDraft.jsブロックへ次のように反映する。

| `article.md` の書き方 | X側の扱い |
|----------------------|-----------|
| `## 見出し` | `header-one`（XのHeading） |
| `### 小見出し` | `header-two`（XのSubheading） |
| 空行なしで続く複数行 | 同じ本文ブロック内のソフト改行（Shift+Enter相当） |
| 同じ話題内の1つの空行 | 同じ本文ブロック内の空行（Shift+Enterを2回押した相当） |
| `---` | `Insert > Divider` 相当の `DIVIDER` atomic block |
| Markdown画像 | `article.md` 上の位置に入れる本文側画像 |

整形ルール:

- 箇条書き、引用例、同じ項目が並ぶ列挙は、空行を挟まず同一ブロック内のソフト改行にする。
- 話題は同じだが段落を分けたい場合は、通常の空ブロックを入れず、同じ本文ブロック内で `\n\n` にする。
- 大きく話題が変わる場合だけ、通常の空ブロックを1つ置き、`DIVIDER` を入れてから次の `header-one` に進む。
- 通常の空ブロックを連続させない。本文全体で、通常の空ブロックは原則 `DIVIDER` の直前だけにする。
- 見出しっぽい行を太字風に見せるだけで済ませず、必ずXのHeading/Subheadingブロックとして登録する。
- `article_plain.txt` に `---` が含まれていても、Xへはハイフン文字列として貼らない。リッチ本文生成時は `article.md` の `---` をDividerブロックとして解釈する。
- ブラウザからファイルへ逆同期する場合は、Draft.jsの `header-one` / `header-two` / `DIVIDER` / `MEDIA` を `article.md` の `##` / `###` / `---` / Markdown画像へ戻す。

## ヘッダー画像

X長文記事のヘッダーは 5:2 で作る。

推奨サイズ:

- `2500x1000`
- `2000x800`
- `1500x600`

ルール:

- 重要な人物・文字・モチーフは中央80%以内に置く
- 端には重要情報を置かない
- デフォルトでは画像内テキストを入れすぎない
- 日本語文字を入れる場合は短いタイトルだけにする
- セミナー内容に関係ない抽象的な装飾だけで終わらせない

Codex/ChatGPTで画像生成する場合は、サブスク内の画像生成機能を優先する。ユーザーが明示しない限り、画像生成API、APIキー、`OPENAI_API_KEY`、課金APIを使わない。画像生成モデルで失敗した場合は、Pillow、SVG、HTMLスクショ、ローカル合成で代替成果物を作らず、生成できなかったことを報告する。

ヘッダープロンプトには必ず次を入れる。

```text
Aspect ratio 5:2. Canvas size 2500x1000. Keep all important subjects and text inside the center safe area.
```

## Kimi WebBridgeでX下書き保存

Xへ記事本文や画像を送信する直前に、ユーザーへ確認する。これは外部サービスへデータを送る操作のため、省略しない。

確認文に含めること:

- Xへ送る内容: タイトル、本文、ヘッダー画像
- 公開はせず下書き保存までに止めること
- `Post` / `Publish` / `投稿する` / `公開` はクリックしないこと
- ヘッダー以外の画像を挿入する場合は、すべて `article.md` のMarkdown画像位置を正として貼り付け挿入すること

Kimi WebBridge の健康確認:

```bash
~/.kimi-webbridge/bin/kimi-webbridge status
```

健康なら、Kimi WebBridge の HTTP API または利用中エージェントのKimiツールで進める。

ブラウザ操作は原則として Vivaldi を使う。X Articles の下書き保存、プレビュー確認、スクリーンショット確認は Vivaldi 上の Kimi WebBridge 接続タブで行い、ユーザーから明示されない限り Chrome へ切り替えない。

基本手順:

1. XのArticles作成画面を開く。UIが変わっている可能性があるため、まずX上で `Articles` / `記事` / `Write` / `作成` を探す。
2. 既存の未送信記事がある場合は、勝手に上書きしない。
3. タイトルを入力する。
4. ヘッダー画像をアップロードする。
5. `article_plain.txt` を本文へ貼る。
6. `article.md` の構造に合わせて、Heading/Subheading、ソフト改行、通常段落、DividerをX本文ブロックへ反映する。
7. 既存下書きを修正している場合は、ブラウザ本文を正として `article_plain.txt` / `article.md` を同期する。
8. `article.md` にMarkdown画像がある場合だけ、下の「ヘッダー以外の画像の安全な挿入手順」に従って画像を入れる。
9. ヘッダー画像が5:2の画像で、本文エディタ外にあることを確認する。
10. Markdown画像数と本文側画像数、各画像の配置を確認する。
11. Heading/Subheading/Dividerの数と配置が `article.md` と一致することを確認する。
12. `Post` / `Publish` / `投稿する` / `公開` はクリックしない。
13. 閉じる操作時に保存確認が出た場合のみ `Save draft` / `下書き保存` を選ぶ。
14. 下書き一覧、URL、またはスクリーンショットで下書き状態を確認する。
15. `draft-save-log.md` に結果を書く。

不明なUI、公開につながりそうなボタン、確認なしで投稿されそうな状態を見つけたら、そこで停止してユーザーに確認する。

## ヘッダー以外の画像の安全な挿入手順

ヘッダー以外の画像は、図解・感想スクショ・実績スクショ・補足画像を含め、すべて `article.md` のMarkdown画像位置を正として挿入する。先に「どこへ画像を入れるか」をMarkdownファイル上で決めてから、同じ位置へブラウザで貼り付ける。

原則:

- ヘッダー画像だけはヘッダー専用file inputを使ってよい。
- ヘッダー以外の画像は、必ず本文エディタへの貼り付けで入れる。
- ヘッダー以外の画像で `upload` ツール、`Insert > Media`、本文用file input、React内部の `onFilesAdded` / `_handleFiles` 直呼びを使わない。
- Kimiの合成pasteが効かない場合だけ、X本文エディタの貼り付け入口である `handlePastedFiles(File[])` を使ってよい。これはアップロード内部処理ではなく、本文エディタのpaste相当として扱う。
- 貼り付けで入らない場合は停止し、ユーザーに状況を報告する。別経路へ勝手に切り替えない。

ヘッダー画像で使ってよいファイル入力:

- ヘッダー専用の `input[type=file]`
- `accept` が `image/jpeg,image/png,image/webp`
- `multiple` が `false`
- `accept` に `video/mp4` や `video/quicktime` を含まない

ヘッダー以外の画像で使ってはいけないもの:

- エディタ上部の `Add Media` / `Insert > Media`
- Kimi WebBridge の `upload` action
- `accept` に `video/mp4` または `video/quicktime` を含む本文メディア入力
- `multiple=true` のファイル入力
- ヘッダー専用ファイル入力
- Draft.js / React props の `onFilesAdded` / `_handleFiles` の直呼び

ヘッダー以外の画像で使う方法:

1. `article.md` に、画像を置きたい位置へMarkdown画像を追加する。
2. `article.md` から `直前の本文ブロック/見出し -> 画像パス` の順序を読む。
3. X本文エディタのDraft.js `editorState` で、Markdown画像の直前にある本文ブロックまたは見出しブロックを探す。
4. 選択位置をそのブロック末尾へ `forceSelection` する。
5. 画像ファイルを `File` と `DataTransfer` に載せ、本文エディタへ `ClipboardEvent('paste')` として送る。Kimiの合成pasteが効かない場合だけ、OSクリップボード + 実キーボード、またはX本文エディタの `handlePastedFiles(File[])` で同じ位置へ貼る。
6. 新しく増えた `atomic` media block を検出する。
7. その新規media blockだけをMarkdown画像の位置へ移動する。
8. 1枚ごとに、ヘッダー画像が本文外の5:2画像のままであること、本文画像数が1増えたことを確認する。

貼り付けで新規media blockが検出できない場合は停止する。file input、`upload`、`Insert > Media`、`onFilesAdded` / `_handleFiles` へフォールバックしない。

最終検証:

- ページ上のヘッダー画像が5:2相当であること（例: `1200x480`, `1983x793`, `2500x1000`）
- ヘッダー画像の `inEditor` が `false` であること
- 本文エディタ内の `img` 件数が `article.md` のMarkdown画像件数と一致すること
- 各本文画像が `article.md` のMarkdown画像位置と一致すること
- `article_plain.txt` の本文がブラウザ本文と一致し、重複していないこと

## Google Driveコピー

成果物を Google Drive へコピーする場合は、次のコマンドをユーザーへ提示するだけにする。エージェント自身では実行しない。

```bash
rclone copy "$TEAM_INFO_ROOT/personal/<account>/outputs/x-long-article-drafts/YYYY-MM-DD/<slug>/" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/X長文記事/<slug>/" --progress
```

rclone が未設定の場合は `.agent/skills/common/git-workflow/gdrive-copy/SKILL.md` の初回セットアップ手順を案内する。

## 完了条件

- Loom・repo内台本のどこを参照したか `sources.md` に残っている
- 5:2ヘッダー画像または生成失敗理由が明確
- `article.md` と `article_plain.txt` が保存されている
- Xへ送信する直前確認をしている
- Xでは公開せず、下書き保存で止めている
- `article.md` のMarkdown画像位置とX本文内画像の配置が一致している
- アプリ記事では、画面構成・できること・裏側の仕組み・人間が確認する場所が説明されている
- ジモティー関連では、投稿管理、地域ローテーション、画像管理、ログ、Drive/シート連携が読者向けに噛み砕かれている
- 専門用語は消しすぎず、用語、寄り添い、簡単な言い換え、例え話または具体例の順で説明されている
- ヘッダー画像が本文画像に置き換わっていない
- `draft-save-log.md` に下書き保存結果と残課題がある
