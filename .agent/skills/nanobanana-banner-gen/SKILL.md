# Nanobanana Banner Gen

スプレッドシートの求人データからバナー画像を自動生成し、Google Driveへのアップロードとスプレッドシートへの埋め込みを一括で行うスキルです。実行コンテキストに応じて、Codex CLI では GPT Image 2、Antigravity / 通常実行では Nanobanana Pro (Gemini 3 Pro Image) を使い分けます。

## 🚀 ハイブリッド・ワークフロー

このスキルは、実行元に応じて画像生成プロバイダを切り替えるハイブリッド方式で動作します。

### 1. タスクの書き出し (Export)
まず、スプレッドシートから未処理の行を抽出してローカルにタスクファイルを生成します。

```powershell
python .agent/skills/nanobanana-banner-gen/scripts/nanobanana_pro_banner.py export
```
- `.agent/skills/nanobanana-banner-gen/tasks/` 配下に `task_XX_type.json` と `task_XX_type.txt` が作成されます。

### 2. ハイブリッド生成 (Generation)
エージェントは書き出されたタスクを一つずつ処理します。

1.  **Codex CLI モード**:
    - Codex CLI 環境では GPT Image 2 を優先して生成します。
    - `python .agent/skills/nanobanana-banner-gen/scripts/nanobanana_pro_banner.py generate --task_id XX_type`
    - `OPENAI_API_KEY` が未設定、または OpenAI 側で失敗した場合は Gemini API にフォールバックします。
2.  **標準モード (Antigravity native)**:
    - `generate_image` ツールを使用して画像を生成します。
    - 出力先: `outputs/nanobanana/{Label}_Job_{Row}.jpg`
3.  **APIモード (Fallback / 強制実行)**:
    - `generate_image` が制限（クォータ上限など）で失敗した場合、即座に以下のコマンドを実行してAPI経由で生成を続行します。
    ```powershell
    python .agent/skills/nanobanana-banner-gen/scripts/nanobanana_pro_banner.py generate --task_id XX_type
    ```
    - `--provider openai` または `--provider gemini` で明示指定できます。
    - `auto` では Codex CLI を検出したときだけ GPT Image 2、それ以外は Gemini API を使います。

### 3. 結果の反映 (Import)
生成されたすべての画像・投稿文章・画像プロンプトをGoogle Driveへアップロードし、スプレッドシートへ一括反映します。

```powershell
python .agent/skills/nanobanana-banner-gen/scripts/nanobanana_pro_banner.py import
```
- 各アカウントのフォルダ（マイドライブ > AI > アカウント名）に自動整理されます。
- スプレッドシートには `=IMAGE("...")` 形式で埋め込まれます。
- 投稿文章は各アカウントフォルダ内に `工場の投稿文章.md` / `在宅1の投稿文章.md` / `在宅2の投稿文章.md` のような名前で保存されます。
- 完了後、Discordへ一括報告が送信されます。

### 4. 反映時の安全確認
- `tasks.json` を唯一の正本として扱い、ファイル名や種別を推測で補正しない。
- `工場.jpg` / `在宅1.jpg` / `在宅2.jpg` は、行の種別ごとに固定対応させる。アカウント名やフォルダ順から逆算しない。
- 投稿文章ファイルも、画像やプロンプトと同じく種別ごとに固定名で保存し、ファイル名を後から推測して変えない。
- 工場案件は `/Users/deguchishouma/team-info/inputs/jmty_factory_cases/2026-02_案件一覧.md` を条件の正本として扱い、`prepare` 時にそこから案件をランダム選択する。
- 途中で追加された条件（例: `GPT image 2` 指定、CTA なし、アカウント名や地域の非表示など）は、既存出力に手作業で足さず、必ず `prepare` から最新条件でやり直す。
- 画像がすでにある場合は、画像 OCR を優先して投稿文章と画像プロンプトを再生成する。画像に書かれている職種・月収・訴求が本文とズレている場合は、本文側を画像に合わせて更新する。
- アカウント名と行番号を必ず突合し、工場/在宅の種別を取り違えない。行がずれていたり、別アカウントの画像や本文が混ざる場合はアップロード前に止める。
- Drive 同期の前に、画像の OCR とファイル名を照合する。工場画像に在宅語が目立つ、または在宅画像に工場語が目立つ場合は、アップロードを止めて該当アカウントだけ修正する。
- 失敗時は手動での部分反映を続けず、`sync-drive` を再実行して同じ manifest から復旧する。

## 🛠️ 事前準備
- **GWS CLI**: `gws.cmd` がパスに通っていること。
- **.env**:
  - Gemini 用: `GEMINI_API_KEY=...`
  - Codex CLI で OpenAI API を使う場合: `OPENAI_API_KEY=...`
  - 任意 override: `NANOBANANA_IMAGE_PROVIDER=openai` または `gemini`
- **Pythonライブラリ**: `requests` がインストールされていること。

## ⚠️ 注意事項
- スプレッドシートの「アカウント情報」シートの A7 行目以降を対象とします。
- すでに `IMAGE` 関数が入っているセルは、デフォルトでスキップされます。強制的に再生成する場合は `--force` オプションを付けて `export` してください。
- `auto` 判定は `CODEX_THREAD_ID` / `CODEX_SANDBOX` / `CODEX_CI` のいずれかがあると Codex CLI 扱いにします。
- 画像内容の確認で不整合が出た場合は、ファイル名を入れ替えて誤魔化さず、元の生成条件を見直して再生成してください。
