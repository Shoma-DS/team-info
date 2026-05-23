---
name: x-long-article-draft-saver
description: Loom MCP の文字起こし、repo 内のセミナー台本、既存Xアカウント設定を参照し、5:2ヘッダー画像とX長文記事を作成して、Kimi WebBridgeでX Articlesへ下書き保存する。AIセミナー記事、限定アーカイブ導線、公式LINEキーワードCTAまで含む投稿準備に使う。
---

# x-long-article-draft-saver スキル

## 役割

Loom MCP の録画文字起こしと repo 内の台本・メモを材料に、X長文記事用のセットを作る。

- 5:2 のヘッダー画像
- X長文記事本文
- X Articles へ貼り付けるプレーンテキスト
- Kimi WebBridge による X 下書き保存
- 保存ログと Google Drive コピー案内

本文だけを作る場合は `x-long-article-writer` を参照する。このスキルは「記事セット作成からX下書き保存まで」の上位ワークフローとして使う。

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

## 参照優先順位

1. ユーザーが今回指定したテーマ・CTA・禁止事項
2. Loom MCP で取得した文字起こし、summary、key takeaways
3. repo 内のセミナー台本・スライド構成・LINE導線
4. 対象Xアカウント設定
5. `.agent/skills/x-long-article-writer/` の記事構成ルール
6. Obsidian の関連ノート

内部パスや作業用語は読者にそのまま見せすぎない。記事内では「実際にセミナーで話したこと」「裏側でやっていること」として自然に翻訳する。

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
- `.agent/skills/x-long-article-writer/`
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

`x-long-article-writer` の構成を基本に、X Articles向けに次の順番で作る。

1. タイトル
2. 冒頭フック
3. 第1回セミナーで伝えた結論
4. 読者の誤解・つまずき
5. Loom文字起こしから拾った具体例
6. repo内台本から拾った手順・比喩・実演
7. 今日から真似できる実践ステップ
8. 第2回アーカイブへの限定CTA

記事本文では、見出しを増やしすぎず、1文を短くする。Markdown版では見出しを使ってよいが、`article_plain.txt` ではXのエディタに貼って崩れにくいプレーンテキストへ整える。

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

Kimi WebBridge の健康確認:

```bash
~/.kimi-webbridge/bin/kimi-webbridge status
```

健康なら、Kimi WebBridge の HTTP API または利用中エージェントのKimiツールで進める。

基本手順:

1. XのArticles作成画面を開く。UIが変わっている可能性があるため、まずX上で `Articles` / `記事` / `Write` / `作成` を探す。
2. 既存の未送信記事がある場合は、勝手に上書きしない。
3. タイトルを入力する。
4. ヘッダー画像をアップロードする。
5. `article_plain.txt` を本文へ貼る。
6. プレビューまたはスクリーンショットで崩れを確認する。
7. `Post` / `Publish` / `投稿する` / `公開` はクリックしない。
8. 閉じる操作時に保存確認が出た場合のみ `Save draft` / `下書き保存` を選ぶ。
9. 下書き一覧、URL、またはスクリーンショットで下書き状態を確認する。
10. `draft-save-log.md` に結果を書く。

不明なUI、公開につながりそうなボタン、確認なしで投稿されそうな状態を見つけたら、そこで停止してユーザーに確認する。

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
- `draft-save-log.md` に下書き保存結果と残課題がある
