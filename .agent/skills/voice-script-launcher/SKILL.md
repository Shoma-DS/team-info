---
name: voice-script-launcher
description: 台本をVOICEVOXで音声化する実行フロー。run.sh実行前に必要な選択肢（台本番号・音声プロファイル番号）を1つずつ確認し、テーマは台本名から自動決定する。初回ならsetup.sh実行後に選択済み入力でrun.shを実行し、2回目以降はrun.shのみ実行する。
---

# 台本音声化 起動スキル

## 目的
- `Remotion/generate_voice.py` を安全に起動する。
- 初回セットアップ漏れを防ぐ。
- `run.sh` 実行後の対話入力をなくし、実行前に全入力を確定する。
- 質問を1つずつ行い、回答しやすくする。
- テーマ入力を省略し、台本名から自動で決める。

## 実行前提
- 作業ディレクトリは `Remotion/`。
- `setup.sh` と `run.sh` が存在すること。

## 必須フロー
1. 実行前に初回起動かどうか確認する。
- 質問: 「今回が初回起動ですか？」

2. `run.sh` 実行前に、質問は必ず1つずつ聞く。
- まず台本ファイル番号だけ聞く。
- 次に音声設定プロファイル番号だけ聞く。
- 同時に複数項目を聞かない。

3. テーマはユーザーに聞かず、選択された台本ファイル名から自動決定する。
- 拡張子（`.txt` / `.md`）を除去する。
- 末尾の日付サフィックス（例: `_20260211`）があれば除去する。
- 例: `地政学_世界を動かす地理の読み方_20260211.md` -> `地政学_世界を動かす地理の読み方`

4. 確定した入力値を `run.sh` に標準入力で一括で渡して実行する。
- 初回（はい / yes）の場合:
```bash
cd Remotion
bash setup.sh
printf '%s\n%s\n%s\n' "<台本番号>" "<プロファイル番号>" "<テーマ>" | bash run.sh
```
- 2回目以降（いいえ / no）の場合:
```bash
cd Remotion
printf '%s\n%s\n%s\n' "<台本番号>" "<プロファイル番号>" "<テーマ>" | bash run.sh
```

5. 途中で `run.sh` 内の再質問が出ても、追加でユーザーに聞かず、先に確定した値で完結させる。

## 失敗時の扱い
- `run.sh` 実行時に `.venv` 不足や依存不足で失敗した場合は、初回扱いとして `setup.sh` 実行を提案し、承認があれば実行する。
- VOICEVOX接続エラー時は、エンジン起動状態 (`http://127.0.0.1:50021`) の確認を案内する。

## Google Driveへの自動コピー（必須）
- `run.sh` が成功して `.wav` ファイルが生成された後、以下のコマンドで Google Drive にコピーする。
- コピー先: `/Users/deguchishouma/Library/CloudStorage/GoogleDrive-syouma1674@gmail.com/マイドライブ/team-info/`
- コマンド例:
```bash
cp "Remotion/output/audio/<生成されたファイル名>.wav" "/Users/deguchishouma/Library/CloudStorage/GoogleDrive-syouma1674@gmail.com/マイドライブ/team-info/"
```
- コピー成功後、「Google Driveにもコピーしました」と報告する。
- コピー失敗時はエラーを報告し、手動コピーのパスを案内する。

## 出力方針
- 実行前に「何を実行するか」を1行で伝える。
- 実行前に「事前確定した入力値」を短く再掲する。
- テーマは「台本名から自動決定した値」として提示する。
- 実行後に成功/失敗を短く報告する。

## フロー変更時の必須同時更新ルール
- 音声化フローの質問順、選択肢、入力項目、実行手順のいずれかを変更した場合は、以下を同じ変更内で必ず更新する。
1. `Remotion/generate_voice.py`（実装）
2. `.agent/skills/voice-script-launcher/SKILL.md`（スキル手順）
3. `Remotion/Voicebox_TTS_Skill_Guide.md`（利用ドキュメント）

- 変更完了前に、次の整合チェックを行う。
1. `generate_voice.py` の実際の質問項目数と `SKILL.md` の事前確認項目数が一致していること。
2. `Voicebox_TTS_Skill_Guide.md` の「実行後に求める入力説明」が最新フローと一致していること。
3. `SKILL.md` の実行コマンド例が最新フロー（事前確定後に一括入力）と一致していること。
