---
name: aoyama-ryusei-voice
description: Remotion/scripts/voice_scripts の台本を VOICEVOX 青山龍星（aoyama_ryuusei_normal）固定で音声生成する。転職・キャリア系ショート動画のナレーション生成、かな版台本優先、VOICEVOX Engine 起動確認、生成後の音声パス確認に使う。
---

# 青山龍星 音声生成スキル

## 目的
- VOICEVOX の `aoyama_ryuusei_normal` プロファイルを固定で使う。
- 転職・キャリア系ショートの男性ナレーションを、毎回プロファイル選択なしで生成する。
- `Remotion/scripts/voice_scripts/<台本名>_kana.md` があれば、読み間違い防止のため自動で優先する。

## 固定設定
- プロファイル: `aoyama_ryuusei_normal`
- 話者: 青山龍星
- スタイル: ノーマル
- 設定ファイル: `Remotion/configs/voice_config.json`
- 出力先: `outputs/sleep_travel/audio/`

## 必須フロー
1. 対象台本を `Remotion/scripts/voice_scripts/` から特定する。
2. 同名の `_kana.md` があるか確認する。ある場合は `generate_voice.py` が自動で使う。
3. VOICEVOX Engine の状態を確認する。
   ```bash
   python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" voicevox-engine-status
   ```
4. `stopped` の場合だけ起動する。
   ```bash
   python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" start-voicevox-engine
   ```
5. 次の形で音声生成を実行する。`<script>` はファイル名、`<theme>` は出力名用の短いテーマにする。
   ```bash
   python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- "$TEAM_INFO_ROOT/Remotion/generate_voice.py" --script "<script>" --profile "aoyama_ryuusei_normal" --theme "<theme>"
   ```
6. 生成ログの `完了! 音声ファイルが` のパスを確認する。
7. 生成後に `_kana.md` が削除された場合は、必要なら台本作成側で再作成する。これは `generate_voice.py` の仕様。

## 実行時の注意
- 長めの台本は 30 秒以上かかる。ユーザーが実行を明示した場合に進める。
- Docker / VOICEVOX は必要時だけ起動する。作業完了後、不要なら停止する。
- 青山龍星以外を使う場合は、このスキルではなく `voice-script-launcher` を使う。
- `VOICEVOXエンジンに接続できません` が出た場合は、Engine 状態確認と起動に戻る。
- `プロファイルが見つかりません` が出た場合は、`Remotion/configs/voice_config.json` に `aoyama_ryuusei_normal` があるか確認する。

## 完了報告
- 台本名
- プロファイル名
- 出力音声パス
- かな版台本が使用されたか
- VOICEVOX Engine を起動したか
