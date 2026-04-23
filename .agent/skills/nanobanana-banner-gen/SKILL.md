# Nanobanana Banner Gen

スプレッドシートの求人データから、Nanobanana Pro (Gemini 3 Pro Image) を用いてバナー画像を全自動生成し、Google Driveへのアップロードとスプレッドシートへの埋め込みを一括で行うスキルです。

## 🚀 ハイブリッド・ワークフロー

このスキルは、**Antigravityの無料枠**と**Gemini API (有料枠/クレジット)** を組み合わせたハイブリッド方式で動作します。

### 1. タスクの書き出し (Export)
まず、スプレッドシートから未処理の行を抽出してローカルにタスクファイルを生成します。

```powershell
python .agent/skills/nanobanana-banner-gen/scripts/nanobanana_pro_banner.py export
```
- `.agent/skills/nanobanana-banner-gen/tasks/` 配下に `task_XX_type.json` と `task_XX_type.txt` が作成されます。

### 2. ハイブリッド生成 (Generation)
エージェントは書き出されたタスクを一つずつ処理します。

1.  **標準モード (Antigravity native)**:
    - `generate_image` ツールを使用して画像を生成します。
    - 出力先: `outputs/nanobanana/{Label}_Job_{Row}.jpg`
2.  **APIモード (Fallback)**:
    - `generate_image` が制限（クォータ上限など）で失敗した場合、即座に以下のコマンドを実行してAPI経由で生成を続行します。
    ```powershell
    python .agent/skills/nanobanana-banner-gen/scripts/nanobanana_pro_banner.py generate --task_id XX_type
    ```
    - このモードは `.env` に設定された `GEMINI_API_KEY` を使用します。

### 3. 結果の反映 (Import)
生成されたすべての画像をGoogle Driveへアップロードし、スプレッドシートへ一括反映します。

```powershell
python .agent/skills/nanobanana-banner-gen/scripts/nanobanana_pro_banner.py import
```
- 各アカウントのフォルダ（マイドライブ > AI > アカウント名）に自動整理されます。
- スプレッドシートには `=IMAGE("...")` 形式で埋め込まれます。
- 完了後、Discordへ一括報告が送信されます。

## 🛠️ 事前準備
- **GWS CLI**: `gws.cmd` がパスに通っていること。
- **.env**: リポジトリルートに `GEMINI_API_KEY=your_key` が設定されていること。
- **Pythonライブラリ**: `requests` がインストールされていること。

## ⚠️ 注意事項
- スプレッドシートの「アカウント情報」シートの A7 行目以降を対象とします。
- すでに `IMAGE` 関数が入っているセルは、デフォルトでスキップされます。強制的に再生成する場合は `--force` オプションを付けて `export` してください。
