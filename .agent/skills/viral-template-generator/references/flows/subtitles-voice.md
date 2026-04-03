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

## テンプレ差分
- `profile.yaml` を読む
- `phase_refs.subtitles_voice` があれば追加で読む
- 差分では字幕レイアウト、名前カード、句読点処理、音声トーンなどを調整する
