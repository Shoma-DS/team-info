---
name: html-to-pdf
description: Convert HTML files to PDF using headless Google Chrome. Preserves full styling, fonts, and layout. Use when the user wants to export a webpage or HTML document as a PDF.
---

# HTML to PDF 変換スキル

## 概要
Google Chrome のヘッドレスモードを使って HTML ファイルを高品質な PDF に変換します。

## 変換コマンド（Python スクリプト）
スキルのディレクトリにある `convert.py` を使って変換します。

```bash
python3 /Users/deguchishouma/team-info/.agent/skills/common/html-to-pdf/convert.py <入力HTMLパス> [出力PDFパス]
```

- 出力パスを省略した場合、入力ファイルと同じフォルダに同名の `.pdf` が作成されます
- A4サイズ・余白なしで出力（クロージング資料など全幅デザイン向け）

## ワークフロー
1. 入力HTMLファイルのパスを確認する
2. `convert.py` を実行する
3. 出力されたPDFのパスをユーザーに伝える

## 注意事項
- Google Chrome が `/Applications/Google Chrome.app/` にインストールされている必要があります
- Webフォント（Google Fonts等）を使用している場合はインターネット接続が必要です
- `file://` プロトコルでフォントが読み込まれない場合は、ローカルサーバーを立ち上げてから変換します
