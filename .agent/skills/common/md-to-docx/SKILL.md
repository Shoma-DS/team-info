---
name: md-to-docx
description: Markdownファイルを Word(.docx) に変換する。見出し・太字・箇条書き・水平線に対応。python-docx を使用。
---

# md-to-docx スキル

## 役割
- `*.md` ファイルを Word形式（`.docx`）に変換して出力する
- frontmatter（`---` で囲まれたブロック）は除外する
- `## 見出し` → Word 見出しスタイル、`**太字**` → 太字、`---` → 区切り線として変換

## スクリプト
- `scripts/md_to_docx.py`

## 使い方（Agent用コマンド）

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/common/md-to-docx/scripts/md_to_docx.py" \
  --input "[入力.md の絶対パス]" \
  --output "[出力.docx の絶対パス]"
```

## 制限
- テーブル・画像・コードブロックは現時点では未対応
- 変換後は Word で開いてフォント・余白を確認すること

## Google Drive アップロード（任意）

```bash
rclone copy "[出力.docx の絶対パス]" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/client_scripts/" --progress
```

rclone 未設定の場合は `.agent/skills/common/gdrive-copy/SKILL.md` を参照。
