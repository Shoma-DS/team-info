# X メトリクス収集スクリプト

このフォルダには、X の投稿の数字を取りに行くスクリプトがあります。
取った数字は Neon PostgreSQL に保存します。

## まずやること

`.env.example` を見ながら、必要な環境変数を自分のパソコンに設定します。
Git に入るファイルへ本物のキーは書かないでください。

置き場所は repo 直下の `.env` を正本にします。
プレビュー画面の環境変数設定UIも、この `.env` を読み書きします。

## ライブラリを入れる

macOS / Linux:

```bash
pip install -r "$TEAM_INFO_ROOT/.agent/skills/x-post-writer/scripts/requirements.txt"
```

Windows:

```powershell
pip install -r "$env:TEAM_INFO_ROOT\.agent\skills\x-post-writer\scripts\requirements.txt"
```

## 実行する

macOS / Linux:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/x-post-writer/scripts/x_metrics_collector.py"
```

Windows:

```powershell
python "$env:TEAM_INFO_ROOT\.agent\skills\x-post-writer\scripts\x_metrics_collector.py"
```

## このスクリプトがやること

1. `accounts_config.json` を読む
2. 対象アカウントの直近3日間のメイン投稿を取る
3. いいねや表示回数などを DB に入れる

ツリー型の投稿は、1投稿目だけを分析対象にします。
X API取得時に返信形式の続き投稿を除外し、DB分析でも続き投稿の数値は追いません。

## ブックマーク取得時の初回セットアップ

`fetch_bookmarks.py` は、初回だけ X API から次の情報も取って `accounts/*.md` の叩き台を作れます。

- 表示名
- ハンドル
- X User ID
- プロフィール文
- 固定投稿

2回目以降は、同じ `X User ID` またはハンドルに一致する既存ファイルを再利用します。
自動取得ブロックだけ更新したい場合は `fetch_bookmarks.py --refresh-account-file` を使います。

ブックマーク取得自体は、プロフィール取得とは別に OAuth 2.0 user token が必要です。
使う環境変数の優先順は次です。

- `X_BOOKMARKS_ACCESS_TOKEN_GUTARAAIKATUYOU`
- `X_OAUTH2_ACCESS_TOKEN_GUTARAAIKATUYOU`
- `X_BEARER_TOKEN`（中身が OAuth 2.0 user token の場合のみ）

## 定時自動化

`scheduled_draft_pipeline.py` は次をまとめて行います。

- 新規ブックマークだけを state 管理で抽出
- Codex を優先して下書き生成
- Codex が token / context 制限や失敗で止まったら Claude Code にフォールバック
- 下書きを Neon DB に保存
- 画像生成用 prompt をファイル保存
- Discord に draft_id / プレビューURL / 画像プロンプトを報告

launchd 用の管理は `manage_launch_agents.py` を使います。

## 定期実行について

`launchd` を使った定期実行の設定は別途案内します。
