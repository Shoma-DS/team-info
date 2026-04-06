---
name: insta-company-secretary-log
description: insta-company の秘書ログを作成し、社長メモ・ToDo・引き継ぎ事項を 1 日単位で整理する。
---

# insta-company-secretary-log スキル

## 役割
- 社長から渡されたメモやタスクを秘書ログへ整理する
- 何をリサーチ部・コンテンツ部へ渡すべきかを切り分ける

## 入力
- 社長のメモ
- 今日やること
- 気づきや仮説

## 手順
1. `insta-company/CLAUDE.md` と `insta-company/employees/secretary/CLAUDE.md` を読む
2. 今日の日付を確認する
3. `insta-company/employees/secretary/logs/YYYY-MM-DD.md` を作るか追記する
4. 次の見出しで整理する
   - 今日の優先事項
   - 未処理タスク
   - 他部署への引き継ぎ
   - アイデアメモ
5. 曖昧な指示は、他部署が動ける形まで整えて書く

## 出力形式
```md
# YYYY-MM-DD

## 今日の優先事項
- ...

## 未処理タスク
- [ ] ...

## 他部署への引き継ぎ
- リサーチ部: ...
- コンテンツ部: ...

## アイデアメモ
- ...
```

## Google Drive 共有が必要なとき
- ログや共有メモを外部保存したい場合は、ユーザーに次を案内する

```bash
rclone copy "$TEAM_INFO_ROOT/insta-company/employees/secretary/logs/[ファイル名].md" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/insta-company/" --progress
```
