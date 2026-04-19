---
name: gws-sheets-duplicate-checker
description: gws CLI で Google スプレッドシートのシート一覧を見ながら、どのシートのどの列組み合わせで重複判定するかを対話的に選び、重複結果を既存列または新規列へ書き込む。`1S` 列へ書く場合は、非重複かつ空欄の行を既定で `1S予定` に補完する。最後に設定をテンプレート保存して繰り返し実行したいときに使う。
---

# gws Sheets Duplicate Checker

## 役割
- `gws` でスプレッドシートのシート一覧とデータを取得する
- 対象シートを番号で選ばせる
- 重複判定に使う列を1つ以上選ばせる
- 重複フラグを書き込む先を、新規列か既存列かで選ばせる
- 実行前に重複グループ数と対象行をプレビューする
- 最後に今回の条件をテンプレート保存して再利用できるようにする

## 想定ユースケース
- 名簿や顧客一覧のメールアドレス重複を確認したい
- 氏名+電話番号の組み合わせ重複を検出したい
- 注文IDや外部管理番号の重複を可視化したい
- 毎週同じ判定条件で重複チェックを回したい

## 使い方
1. まずスプレッドシートURLを渡す
2. 保存済みテンプレートを使うか、新規で条件を決めるか選ぶ
3. シート一覧から対象シートを選ぶ
4. 重複判定列を複数選択する
5. 重複結果の書き込み先を決める
6. プレビュー内容を確認して、必要ならシートへ反映する
7. 最後にテンプレート保存するか決める

## 最短コマンド
```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/common/gws-sheets-duplicate-checker/scripts/check_sheet_duplicates.py" \
  --spreadsheet-url "https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit"
```

## テンプレート再実行
テンプレート保存後は、同じスプレッドシート構造に対してテンプレート名を指定して再実行できる。

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/common/gws-sheets-duplicate-checker/scripts/check_sheet_duplicates.py" \
  --spreadsheet-url "https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit" \
  --template-name "<保存したテンプレート名>" \
  --apply-write
```

- `--apply-write` を付けると、テンプレート内容でそのまま書き込みまで進む
- テンプレートのシート名や列名が見つからない場合はエラーで止める

## テンプレート保存
- 保存先は `templates/user-presets/*.json`
- 保存内容:
  - 対象シート名
  - 重複判定列
  - 書き込み先モード (`new_column` / `existing_column`)
  - 書き込み先列名または新規列ヘッダ名
  - 空欄だけの行を除外するか

## 判定ルール
- 選んだ列の値を結合して重複キーを作る
- 前後の空白は除去して判定する
- 新規で条件を決めるとき、`uid` 列があれば既定でそれを重複判定列にする
- 選んだ列がすべて空欄の行は、既定で判定対象から外す
- 行番号が最小の最初の1件は既定で重複扱いしない
- 2件目以降の行だけ `重複` を書く
- 既存列へ書く場合、重複でない行は既存値をそのまま残す
- 既存列 `1S` へ書く場合、重複でない行の `1S` が空欄なら既定で `1S予定` を入れる
- 既存列に `重複` が入っているのに、実際は初回行または非重複行だったケースは Markdown レポートへ保存する

## 実装メモ
- 読み取りは `gws sheets spreadsheets get` と `gws sheets spreadsheets values get`
- 列追加は `gws sheets spreadsheets batchUpdate`
- 値書き込みは `gws sheets spreadsheets values batchUpdate`
- 既存列へ書くときは既存値を上書きするため、非空セルがある場合は確認を入れる
