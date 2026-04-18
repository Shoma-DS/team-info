---
name: nanobanana-banner-gen
description: スプレッドシートから求人投稿文を読み取り、Nanobanana Pro (Gemini 3 Pro) を用いて全自動でバナー画像を生成し、Google Driveへのアップロードと対象シートへの埋め込みを一括で行うスキル。全件一括処理と一部選択処理に対応。
---

# nanobanana-banner-gen

## 概要
Googleスプレッドシートの求人投稿文（工場および在宅）から自動的にバナー画像（正方形 1:1）を生成し、Google Driveの特定フォルダに保存後、同シートの「使用画像」列に自動挿入します。
画像の生成には `generate_image` ツールを使用し、Driveへのアップロードとシートの操作は `gws.cmd` CLI（とPythonスクリプト）経由で行います。

## 対象情報
- **スプレッドシートID**: `1GKBTHwBS6W0D30X_yK7vqsaDRWw3p1tXM7lnFhyb0Uw`
- **シート名**: `アカウント情報` (実際のデータは7行目〜)
- **親フォルダ**: ジモティー画像 (`16P5sOzyJHLemwURON6Wf1i7NjodK3WWF`)

## アカウント（B列）と各求人の列マッピング

- **アカウント名**: B列 (7行目以降)

### ① 工場求人
- **Drive保存先**: `1Tf22McdnA3P4dbcS7COan_RFYXZ-6eXh` （「工場」フォルダ）
- **読み込み元 (投稿文)**: J列
- **挿入先 (使用画像)**: I列

### ② 在宅求人
- **Drive保存先**: `1SNYJWnxZs6MnnH4CAGVAbjJGqGTXzCtr` （「在宅」フォルダ）
- **読み込み元1 (投稿文①)**: S列
- **挿入先1 (使用画像①)**: R列
- **読み込み元2 (投稿文②)**: U列
- **挿入先2 (使用画像②)**: T列

---

## エージェント実行フロー（使い方）

このスキルはAIエージェントが自律的にツールを組み合わせて処理を行います。ユーザーから実行指示があった際、以下の手順に沿って進行してください。

> **⚠️ 注意事項**
> WindowsのPowerShellでは `gws.cmd` へ複雑なJSON文字列(`--params`)を直接渡すとパースエラーになります。情報の取得・更新・アップロードには **必ず一時的なPythonスクリプトを作成・実行** して連携してください。

### 0. 引き継ぎの確認（開始前の必須手順）
実行開始直後に、必ず `.agent/skills/nanobanana-banner-gen/handoff.json` が存在するか確認してください。

- **ファイルが存在する場合**: 
  - ユーザーに「前回の作業が中断されています。**続きから再開**しますか？**最初から**やり直しますか？」と確認してください。
  - 「続きから」の場合、`handoff.json` 内の `target_rows` から `completed_rows` を除いた行を処理対象とします。
- **ファイルが存在しない場合**: 
  - 通常どおり「1. 処理範囲の確認」へ進みます。

### 1. 処理範囲の確認（全件 or 一部）
引き継ぎを行わない場合、ユーザーに以下のように質問します。
> 「バナー作成処理を開始します。**すべてのアカウント（全件）** 作成しますか？それとも **一部のアカウント** だけ作成しますか？」

### 2. 対象行の特定
**【「一部」とユーザーが答えた場合】**
- B列（7行目以降）のアカウント情報を取得します。（※空白セルは弾く）
- 取得したアカウント名をチャット上に **番号付きのリスト（1. Sho, 2. Akko... など）で提示** し、ユーザーに「どのアカウントを処理しますか？（複数選択可）」と聞きます。
- ユーザーの選択を基に、処理する「行番号」のリストを作成します。

**【「全件」とユーザーが答えた場合】**
- B列に名前が入っているすべての行番を処理 대상行のリストとします。

### 3. バナー生成と反映のループ実行
特定した対象行に対して順番に処理を行います。

> [!TIP]
> **枚数が5枚以上ある場合は、5枚ずつのグループ（バッチ）に分けて実行** してください。これにより、AIの生成品質を一定に保ち、タイムアウトなどの接続エラーを回避して確実に完遂できます。

各行・各項目において、以下の手順を繰り返します。（投稿文が空欄の箇所はスキップします）

#### A. データ取得
対象行の、J列(工場)、S列(在宅1)、U列(在宅2) の投稿文をPythonスクリプト（`gws.cmd ... get`）で読み取ります。文字化け防止のため `sys.stdout.reconfigure(encoding='utf-8')` を使ってください。

#### B. 画像生成 (`generate_image`)
読み取った投稿文をもとに、求人の内容にあった魅力的な「正方形(1:1)」のバナー画像を生成し、保存します。（工場用なら1枚、在宅用なら最大2枚の画像が作られます）

#### C. Driveへのアップロード & 権限付与
生成した画像を、求人種別（工場用 / 在宅用）のフォルダIDへアップロードし、権限を付与します。
```python
import subprocess, json
# 画像アップロード
cmd = ["gws.cmd", "drive", "files", "create", "--upload", "画像パス", "--params", json.dumps({"name": "row_X_banner.png", "parents": ["ターゲットフォルダID"]})]
res = subprocess.run(cmd, capture_output=True, text=True)
file_id = json.loads(res.stdout)["id"]

# シート閲覧用として全員へ閲覧権限を付与
subprocess.run(["gws.cmd", "drive", "permissions", "create", file_id, "--params", json.dumps({"role": "reader", "type": "anyone"})])
print("FILEID=" + file_id)
```

#### D. シートへの画像埋め込み
取得したファイルIDを使って `=IMAGE("https://drive.google.com/uc?id={file_id}")` の関数文字列を作成し、該当する「使用画像」列（工場:I列、在宅1:R列、在宅2:T列）に書き込みます。
```python
import subprocess, json
payload = {
    "spreadsheetId": "1GKBTHwBS6W0D30X_yK7vqsaDRWw3p1tXM7lnFhyb0Uw",
    "range": "アカウント情報!I10", # 例: 10行目の工場画像
    "valueInputOption": "USER_ENTERED",
    "values": [[f'=IMAGE("https://drive.google.com/uc?id=FILE_ID")']]
}
subprocess.run(["gws.cmd", "sheets", "spreadsheets", "values", "update", "--params", json.dumps(payload)])
```

#### E. 進捗の記録（引き継ぎ用）
1アカウント（その行のすべての画像）の処理が完了するたびに、`.agent/skills/nanobanana-banner-gen/handoff.json` を更新してください。
```json
{
  "target_rows": [7, 8, 9, 10, ...],
  "completed_rows": [7, 8, ...],
  "last_update": "2026-04-18T12:34:56"
}
```

### 4. チームへの通知（Discord）
画像の更新内容（アカウントごとの変更詳細）をDiscordの専用チャンネルに通知します。
**5枚のバッチ処理ごと、または最終的な完了時**に、以下の集約報告スクリプトを1回実行してください。

```python
import subprocess
import json

# 通知内容のリストをJSON形式で渡します
updates = [
    {"account": "@Sho", "type": "factory"},
    {"account": "@Sho", "type": "remote1"},
    {"account": "@Akko", "type": "factory"}
]

cmd = [
    "python", 
    "scripts/discord/banner_batch_report.py", 
    "--json", json.dumps(updates)
]
subprocess.run(cmd)
```

### 5. 完了報告とクリーンアップ
すべての対象行の生成・反映・通知が終わったら、以下の処理を行って完了です。
- **引き継ぎファイルの削除**: `.agent/skills/nanobanana-banner-gen/handoff.json` を削除します。
- **ユーザーへの報告**: スプレッドシート上での最終確認を促します。
