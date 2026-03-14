---
name: gdrive-copy
description: ローカルのファイルやフォルダを Google Drive の team-info フォルダにコピーするスキル。フォルダごとコピーかファイル選択コピーかをユーザーに確認してから実行する。
---

# Google Drive コピースキル

## 目的

`マイドライブ/team-info`（フォルダID: `1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t`）へ
ローカルのファイル・フォルダをコピーする。

## 前提条件

- **Google Drive for Desktop** が起動していること
- コピー先マウントパス:
  `/Users/deguchishouma/Library/CloudStorage/GoogleDrive-syouma1674@gmail.com/マイドライブ/team-info`

## 実行コマンド

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/common/gdrive-copy/scripts/gdrive_copy.py"
```

## 動作フロー

1. **コピーモード選択**
   - `1` フォルダごとコピー
   - `2` ファイル・フォルダを番号で選択コピー

2. **コピー元パス入力**
   - 絶対パス、または `team-info` ルートからの相対パスで指定
   - 例: `Remotion/my-video/out`、`outputs/viral/renders`

3. **ファイル選択**（モード2のみ）
   - 番号（複数はカンマ区切り）または `all` で全選択

4. **コピー先サブフォルダ**
   - `team-info/` 直下なら Enter、サブフォルダ名を入力して掘り下げることも可能

5. **確認後に実行** → macOS 通知で完了を知らせる

## スキル発動トリガー

ユーザーが以下のような発言をしたとき:
-「Google Drive にコピーして」
- 「team-info の Drive フォルダに送って」
- 「gdrive に上げて」
- 「Drive にアップロードして」

## エラー対処

| エラー | 対処 |
|---|---|
| `Google Drive フォルダが見つかりません` | Google Drive for Desktop を起動してもらう |
| `パスが見つかりません` | パスを再確認してもらう |
