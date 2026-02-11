---
name: voice-script-launcher
description: 台本をVOICEVOXで音声化する実行フロー。初回起動かどうかを確認し、初回ならsetup.sh実行後にrun.sh、2回目以降はrun.shのみ実行する。
---

# 台本音声化 起動スキル

## 目的
- `Remotion/generate_voice.py` を安全に起動する。
- 初回セットアップ漏れを防ぐ。

## 実行前提
- 作業ディレクトリは `Remotion/`。
- `setup.sh` と `run.sh` が存在すること。

## 必須フロー
1. ユーザーに確認する。
- 質問: 「今回が初回起動ですか？」

2. 回答が初回（はい / yes）の場合。
- 以下を順番に実行する。
```bash
cd Remotion
bash setup.sh
bash run.sh
```

3. 回答が2回目以降（いいえ / no）の場合。
- 以下を実行する。
```bash
cd Remotion
bash run.sh
```

## 失敗時の扱い
- `run.sh` 実行時に `.venv` 不足や依存不足で失敗した場合は、初回扱いとして `setup.sh` 実行を提案し、承認があれば実行する。

## 出力方針
- 実行前に「何を実行するか」を1行で伝える。
- 実行後に成功/失敗を短く報告する。
