# subtitles-voice

## 目的
- `script.md` から `script_hiragana.md`、`subtitles.json`、ナレーション音声を作る

## 標準出力
- `script_hiragana.md`
- `subtitles.json`
- narration audio under the selected output folder

## 標準手順
1. Convert the script to hiragana
2. Review and repair pronunciation manually where needed
3. Generate subtitle segments
4. Split long subtitles into card-friendly units
5. Synthesize narration with VOICEVOX
6. Sync subtitle timing to the final audio

## 標準ルール
- 句読点だけのカードを残さない
- 固有名詞は途中で分割しない
- 1〜2 行のカードを優先する
- 読み修正後は字幕文面も実際の読みと合わせる

## 主なスクリプト
- `scripts/convert_to_hiragana.py`
- `scripts/split_subtitles.py`
- `scripts/generate_viral_voice.py`
- `scripts/sync_subtitles_to_audio.py`
- `scripts/align_subtitles_to_audio.py` when postprocessing is needed

## 音声ルール
- VOICEVOX は必要なときだけ起動する
- 使い終わったら停止する
- 合成前にテンプレのトーンに合う音声プロファイルを選ぶ
- `profile.yaml` に `voice_profile` が指定されている場合は、ユーザーが明示的に別話者を指定しない限り必ずそのプロファイルを使う
- 転職・キャリア系のテンプレートでは、明示指示がない限り `aoyama_ryuusei_normal`（青山龍星 / ノーマル）を使う
- `generate_viral_voice.py` は VOICEVOX 起動直後の `ConnectionResetError` を吸収して `/version` 応答まで待つため、同じコマンドを連打しない
- 既定は高速化のため `--fit-target-mode fast`。尺に厳密に合わせたい場合だけ `--fit-target-mode exact` を付ける
- 既定の並列数は `--jobs 2`。PC負荷が高い、または VOICEVOX が不安定なら `--jobs 1` に下げる

## 転職・キャリア系の推奨音声生成コマンド

```bash
python "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/generate_viral_voice.py" \
  --script "$TEAM_INFO_ROOT/[script.md]" \
  --output-dir "$TEAM_INFO_ROOT/Remotion/my-video/public/audio/[動画フォルダ]" \
  --profile aoyama_ryuusei_normal \
  --jobs 2 \
  --fit-target-mode fast
```

## テンプレ差分
- `profile.yaml` を読む
- `phase_refs.subtitles_voice` があれば追加で読む
- 差分では字幕レイアウト、名前カード、句読点処理、音声トーンなどを調整する
