# timing

## 目的
- Composition 完成後にテンポを締め、必要なら字幕整列と render まで進める

## 標準手順
1. Run jet cut as dry-run
2. Apply jet cut if it helps
3. Run subtitle-to-audio alignment when needed
4. Check for too-short subtitle segments
5. Validate TSX and duration updates
6. Render only when the user asks for the final output

## 標準ルール
- 変更系のタイミング処理は dry-run を先に行う
- スクリプトが作るバックアップを残す
- 名前カードやセクション開始がズレたら render 前に直す
- タイミング調整のためだけに字幕文面を結合しない

## 主なスクリプト
- `scripts/jet_cut.py`
- `scripts/align_subtitles_to_audio.py`

## テンプレ差分
- `profile.yaml` を読む
- `phase_refs.timing` があれば追加で読む
- 差分は cut の強さや render 前確認事項に絞る
