---
name: youtube-auto-upload
description: YouTube Data API v3を使用して、動画をYouTubeへ自動アップロード・公開予約する。複数アカウントの切り替えに対応。
---

# YouTube 自動アップロードスキル

## 概要
Google API を使用して、動画を指定した YouTube チャンネルへアップロードします。
即時公開、限定公開、非公開、および指定日時での公開予約に対応しています。

## 依存関係
- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth-httplib2`

## セットアップ手順

### 1. Google Cloud Console での設定
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成。
2. **YouTube Data API v3** を有効化。
3. **OAuth 同意画面** を設定（外部・テストユーザーとして自分のメールアドレスを追加）。
4. **認証情報** から「OAuth 2.0 クライアント ID」を作成（デスクトップアプリ）。
5. JSON をダウンロードし、`client_secrets.json` として保存。

### 2. 認証情報の配置
アカウントごとに以下のディレクトリに `client_secrets.json` を配置してください。

```
~/.config/team-info/youtube-upload/[アカウント名]/client_secrets.json
```

例: `acoriel`, `sleep_travel`

## 使い方

### インタラクティブモード
レンダリング後に自動で起動するか、以下のコマンドで直接起動します。

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/common/youtube-auto-upload/scripts/youtube_uploader.py"
```

### コマンドライン引数
自動実行時に使用します。

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/common/youtube-auto-upload/scripts/youtube_uploader.py" \
  --file "[動画パス]" \
  --account "acoriel" \
  --title "動画タイトル" \
  --description "動画の説明" \
  --privacy "public" \
  --publish-at "2024-04-10T18:00:00Z"
```

## 運用ルール
- 秘密情報（`client_secrets.json`, `token.json`）は絶対リポジトリに含めない。
- `~/.config/team-info/youtube-upload/` を正本として管理する。
- アップロード前に必ずユーザーに確認を取る。
