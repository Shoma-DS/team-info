# Discord Webhook設定手順

このマニュアルは、`team-info` で `/git` のあとに Discord へ報告を送りたい人向けの手順書です。`/git-nd` では報告しません。

2026-04-01 時点で、Discord の公式ヘルプページと公式開発者ドキュメントを確認して作成しています。

---

## まず知っておくこと

- Webhook は、ほかのサービスやスクリプトから Discord のチャンネルへ自動でメッセージを送るための仕組みです。
- Discord の公式ドキュメントでは、Webhook は Bot ユーザーなしでも使える仕組みとして説明されています。
- Webhook URL は**秘密の合言葉**のようなものです。
- URL を知っている人はその Webhook で投稿できるので、URL は他の人に見せないでください。
- いまの `team-info` では、チームで同じ URL を使うなら `config/discord-git-webhook.json` を Git 共有の正本にできます。

---

## 事前に必要なもの

1. Discord サーバーに入っていること
2. そのサーバーで Webhook を作れる権限があること
   - Discord の公式開発者ドキュメントでは、Webhook の作成に `MANAGE_WEBHOOKS` 権限が必要と案内されています
3. 投稿先にしたいテキストチャンネルを決めていること
4. `TEAM_INFO_ROOT` が使える状態で `team-info` を開いていること

---

## 全体の流れ

```text
DiscordでWebhookを作る
→ Webhook URLをコピーする
→ team-info の共有設定ファイルへURLを入れる
→ 状態を確認する
→ /git の報告に使う
```

---

## ① DiscordでWebhookを作る

1. Discord で、報告を送りたいサーバーを開く
2. サーバー名をクリックして、`サーバー設定` を開く
3. 左側メニューから `連携サービス` を開く
4. `Webhooks` を開く
5. `Webhookを作成` または `Create Webhook` を押す
6. 作られた Webhook を開いて、次を決める
   - 名前
   - アイコン
   - 投稿先チャンネル
7. `Webhook URLをコピー` を押す

ここでコピーした URL が、あとで `team-info` に登録する値です。

---

## ② team-info の共有設定ファイルへWebhook URLを入れる

コピーした Webhook URL を、次のコマンドで repo の共有設定ファイルへ保存します。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-set --url "https://discord.com/api/webhooks/ここにコピーしたURL"
```

ポイント:

- URL は `config/discord-git-webhook.json` に保存されます
- このファイルは Git に入るので、repo を見られる人はその URL を使えてしまいます
- そのため、投稿先は Discord の報告専用チャンネルにしておくのがおすすめです
- 個人だけで一時的に変えたいときは、あとからローカル設定や環境変数で上書きできます

保存先のパスを見たいとき:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-path
```

---

## ③ ちゃんと登録できたか確認する

次のコマンドで状態を確認します。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-status
```

見え方の例:

- `configured:repo-shared:...` → 共有設定ファイルが使われています
- `configured:local-state:...` → 登録できています
- `not-configured` → まだ登録されていません

---

## ④ /git の報告で使う

Webhook を登録したあと、`team-info` 側の Discord 報告機能が使えるようになります。
`/git` では、報告するかどうかを聞かれたときに使います。`/git-nd` では使いません。

この repo で使う主なコマンドは次の 4 つです。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-set --url "..."
```

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-status
```

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-clear
```

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-clear
```

- `discord-git-webhook-clear` は、個人のパソコンだけで入れた一時上書きを消したいときに使います

補足:

- 現在の `team-info` では、Discord 報告文はコミットメッセージと変更ファイル名から作られます
- 送る文は、小学生にもわかりやすい短い説明になるように整えられます
- Webhook が未設定なら、Git の push 自体は成功のまま、Discord 送信だけスキップされます
- 読み取り順は `--webhook-url` → 環境変数 → `config/discord-git-webhook.json` → ローカル設定 です

---

## ⑤ Webhook URLを変えたいとき

### Discord 側で変える

1. `サーバー設定` → `連携サービス` → `Webhooks` を開く
2. いまの Webhook を削除するか、新しく作り直す
3. 新しい URL をコピーする

### team-info 側で入れ直す

まず共有設定を消します。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-clear
```

そのあと、新しい URL をもう一度登録します。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-set --url "新しいWebhook URL"
```

---

## ⑥ うまくいかないとき

### `Webhookを作成` が出てこない

- `連携サービス` を開けているか確認する
- サーバーで Webhook を作る権限があるか確認する
- Discord の公式開発者ドキュメントでは、作成に `MANAGE_WEBHOOKS` 権限が必要です

### URL を登録したのに送られない

1. 次のコマンドで `configured:...` になっているか確認する

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-status
```

2. Webhook の投稿先チャンネルが合っているか確認する
3. `config/discord-git-webhook.json` に間違った URL を入れていないか確認する
4. 個人のローカル設定で別の URL を上書きしていないか確認する
5. 心配なら Webhook を作り直して、URL を再登録する

### URL をうっかり誰かに見せてしまった

その URL はもう安全ではない前提で動いてください。

1. Discord の `Webhooks` 画面で、その Webhook を削除する
2. 新しい Webhook を作る
3. 新しい URL を `discord-git-webhook-shared-set` で登録し直す

---

## 覚えておくと安心なこと

- Webhook URL はパスワードに近い扱いで考える
- URL をチャットやスクリーンショットに出さない
- Git 共有する場合は、repo 参加者みんながその URL で投稿できる前提で運用する
- いらなくなった Webhook は Discord 側で削除してよい
- サーバーの連携数には上限があります
  - Discord 公式ヘルプでは、サーバーの連携は最大 50 個と案内されています

---

## 参考にした公式ページ

- Discord 公式ヘルプ: [Server Integrations Page](https://support.discord.com/hc/ja/articles/360045093012-Server-Integrations-Page)
- Discord 公式ヘルプ: [タイトル: Webhooksへの序章](https://support.discord.com/hc/ja/articles/228383668-%E3%82%BF%E3%82%A4%E3%83%88%E3%83%AB-Webhooks%E3%81%B8%E3%81%AE%E5%BA%8F%E7%AB%A0)
- Discord 公式開発者ドキュメント: [Webhook Resource](https://docs.discord.com/developers/resources/webhook)
