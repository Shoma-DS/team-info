# timing

## 目的
- Composition 完成後にテンポを締め、必要なら字幕整列と render まで進める

## 標準手順
1. Run jet cut as dry-run
2. Apply jet cut if it helps
3. Run subtitle-to-audio alignment when needed
4. Check for too-short subtitle segments
5. Validate TSX and duration updates
6. Run final quality verification with the scoring criteria
7. Render only when the user asks for the final output

## 標準ルール
- 変更系のタイミング処理は dry-run を先に行う
- スクリプトが作るバックアップを残す
- 名前カードやセクション開始がズレたら render 前に直す
- タイミング調整のためだけに字幕文面を結合しない
- 最終確認では `remotion-short-sound-design/references/templates/viral-short-vertical.md` の採点基準を必ず読む
- 音声と字幕のズレ、字幕の行数/長さ、画像と字幕の重なり、画像サイズの小ささは render 前の必須チェックにする
- 自動検証で warning / fail が出た場合、原因と対象フレームを直してから再検証する

## 主なスクリプト
- `scripts/jet_cut.py`
- `scripts/align_subtitles_to_audio.py`
- `scripts/verify_viral_short_quality.py`

## 最終品質検証

採点基準:
- `.agent/skills/remotion/video-production/remotion-short-sound-design/references/templates/viral-short-vertical.md`

最低限見る項目:
- 音声尺と composition 尺が合っているか
- `SUBTITLE_TIMELINE` の最終字幕が音声末尾より大きくズレていないか
- 字幕カードが短すぎる / 長すぎる / 2-3行を超えていないか
- 字幕表示が音声より遅れて見えそうな場合、数フレーム前倒しできているか
- 画像と字幕が重なっていないか、最低 50px 以上の余白があるか
- 画像が縦画面で小さすぎないか、横長写真でも幅 85-92% を目安にできているか
- フック、章開始、CTA の代表フレーム still を確認したか

推奨コマンド:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/verify_viral_short_quality.py" \
  --tsx "$TEAM_INFO_ROOT/Remotion/my-video/src/viral/[Composition].tsx" \
  --audio "$TEAM_INFO_ROOT/Remotion/my-video/public/audio/[project]/narration.wav" \
  --subtitles "$TEAM_INFO_ROOT/Remotion/my-video/src/viral/generated/[Subtitles].ts" \
  --duration-frames [frames] \
  --fps 30 \
  --report "$TEAM_INFO_ROOT/outputs/viral-quality/[project]_quality_report.md"
```

`--still-dir` を渡した場合は、代表 still の目視チェック欄も report に追加する。

## テンプレ差分
- `profile.yaml` を読む
- `phase_refs.timing` があれば追加で読む
- 差分は cut の強さや render 前確認事項に絞る
