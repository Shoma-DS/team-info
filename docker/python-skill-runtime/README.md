# Python Skill Runtime

標準の Python/スクリプト系スキルは、この Docker イメージ経由で実行する。

## ビルド

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" build-remotion-python
```

## VOICEVOX Engine

GUI 版ではなく、Docker 上の `VOICEVOX Engine` を使う。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" start-voicevox-engine
```

状態確認:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" voicevox-engine-status
```

停止:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" stop-voicevox-engine
```
