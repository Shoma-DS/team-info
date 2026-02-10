---
name: git-workflow
description: Git のブランチ操作、コミット、プッシュなどのワークフロー。コードの変更をリモートリポジトリに反映するときに使用します。
---

# Git ワークフロースキル

## リモートリポジトリ情報
- **メインリポジトリ**: `https://github.com/Shoma-DS/team-info.git`
- リモート名: `shoma-repo`（ACE-Step-1.5 ディレクトリで設定済み）

## 基本操作

### 新しいブランチを作成してプッシュ
```bash
git checkout -b <ブランチ名>
git add .
git commit -m "コミットメッセージ"
git push -u shoma-repo <ブランチ名>
```

### 変更をコミットしてプッシュ
```bash
git add .
git commit -m "コミットメッセージ"
git push
```

## 注意事項
- コミットメッセージは日本語でも英語でもOK
- `origin` は公式の `ace-step/ACE-Step-1.5` リポジトリ（読み取り専用）
- `shoma-repo` がユーザーのリポジトリ（書き込み可能）
- プッシュ時に認証が必要な場合がある（ユーザーにターミナルでの手動実行を依頼）
