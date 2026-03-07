---
name: voice-script-launcher
description: 台本をVOICEVOXで音声化する実行フロー。MCPツールを活用し、スピーカー確認・テスト音声・本番生成を行う。初回は共通ランタイム経由で `Remotion/.venv` を自動作成する。
---

# 台本音声化 起動スキル

## 目的
- VOICEVOX MCPツールを活用して台本を音声化する。
- 初回セットアップ漏れを防ぐ。
- MCPツールで軽い操作（スピーカー確認・テスト音声）を直接行い、本番生成はPythonスクリプトの並列処理を活用する。

## 実行前提
- 作業ディレクトリはリポジトリルートを基準にする。
- Python 実行は `python .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- ...` を使う。
- VOICEVOXエンジンが `http://127.0.0.1:50021` で起動していること。
- VOICEVOX MCPサーバーがビルド済みであること（`mcp-servers/voicevox/dist/index.js`）。

## 利用するMCPツール

| ツール名 | 用途 |
|---|---|
| `voicevox_get_speakers` | 利用可能なスピーカー・スタイル一覧を取得 |
| `voicevox_get_presets` | プリセット一覧を取得 |
| `voicevox_get_profiles` | voice_config.json のプロファイル一覧を取得 |
| `voicevox_test_speech` | 短いテキストを試し聞き（200文字以内） |
| `voicevox_generate_full` | 台本ファイルを指定して一括音声生成（並列処理） |

## 必須フロー

### 1. 初回起動判定（自動）
- スキルディレクトリ内に `.setup_completed` ファイルが存在するか確認する。
- **存在しない場合（初回）**:
  1. 次のコマンドを実行する。
     ```bash
     python .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- -m pip install requests
     ```
  2. このコマンドは `Remotion/.venv` がなければ自動作成し、その仮想環境へ `requests` をインストールする。
  3. 成功したら `.setup_completed` を作成する。
  4. 次へ進む。
- **存在する場合（2回目以降）**:
  1. そのまま次へ進む。

### 2. VOICEVOXエンジンの接続確認
- `voicevox_get_speakers` を実行して接続を確認する。
- エラーの場合は「VOICEVOXエンジンを起動してください」と案内する。

### 3. プロファイル確認
- `voicevox_get_profiles` でプロファイル一覧を取得し、ユーザーに提示する。
- ユーザーに使用するプロファイルを選択してもらう。

### 4. 台本ファイルの選択
- `Remotion/scripts/voice_scripts/` 内のファイル一覧を提示する。
- ユーザーに使用する台本を選択してもらう。

### 5. テーマの自動決定
- テーマはユーザーに聞かず、選択された台本ファイル名から自動決定する。
- 拡張子（`.txt` / `.md`）を除去する。
- 末尾の日付サフィックス（例: `_20260211`）があれば除去する。
- 例: `地政学_世界を動かす地理の読み方_20260211.md` -> `地政学_世界を動かす地理の読み方`

### 6. テスト音声の確認（任意）
- ユーザーに「テスト音声を生成しますか？」と確認する。
- 希望する場合、台本の冒頭1文を `voicevox_test_speech` で生成して確認してもらう。
- テスト音声で問題があればプロファイルを変更できる。

### 7. 本番音声生成
- `voicevox_generate_full` を実行する。
  - `script_name`: 選択された台本ファイル名
  - `profile_name`: 選択されたプロファイル名
  - `theme`: 自動決定されたテーマ名

### 8. 共有ストレージへの自動コピー（必須）
- `voicevox_generate_full` が成功して `.mp3` ファイルが生成された後、以下のコマンドで共有ストレージへコピーする。
- コピー先は `TEAM_INFO_SHARED_ROOT` を優先し、未指定なら一般的な Google Drive / OneDrive 配下の `team-info/` を自動検出する。
- 自動検出できない場合は `TEAM_INFO_SHARED_ROOT=/path/to/team-info` を設定してから再実行する。
- コマンド例:
```bash
python .agent/skills/common/scripts/team_info_runtime.py copy-to-shared "outputs/sleep_travel/audio/<生成されたファイル名>.mp3"
```
- コピー成功後、「共有ストレージにもコピーしました」と報告する。
- コピー失敗時はエラーを報告し、手動コピーのパスを案内する。

## 失敗時の扱い
- `voicevox_generate_full` 実行時に `.venv` 不足や依存不足で失敗した場合は、初回扱いとして `python .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- -m pip install requests` を提案し、承認があれば実行する。
- VOICEVOX接続エラー時は、エンジン起動状態 (`http://127.0.0.1:50021`) の確認を案内する。

## 出力方針
- 実行前に「何を実行するか」を1行で伝える。
- プロファイル名、台本名、テーマを短く再掲する。
- 実行後に成功/失敗を短く報告する。

## フロー変更時の必須同時更新ルール
- 音声化フローの質問順、選択肢、入力項目、実行手順のいずれかを変更した場合は、以下を同じ変更内で必ず更新する。
1. `Remotion/generate_voice.py`（実装）
2. `.agent/skills/remotion/voice-script-launcher/SKILL.md`（スキル手順）
3. `Remotion/Voicebox_TTS_Skill_Guide.md`（利用ドキュメント）
