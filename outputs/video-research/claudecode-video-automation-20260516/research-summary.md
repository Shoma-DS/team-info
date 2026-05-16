# ClaudeCode動画制作自動化リサーチ 2026-05-16

## 参照

- YouTube: https://www.youtube.com/watch?v=JirJD6IM4fQ
- NotebookLM: https://notebooklm.google.com/notebook/6a21c892-d979-4533-a035-e8f2cb08a65e
- 1秒ごとの確認フレーム: `/tmp/team-info-youtube-frames-JirJD6IM4fQ-ffmpeg/`
- 代表コンタクトシート: `/tmp/team-info-youtube-frames-JirJD6IM4fQ-ffmpeg/contact_sheet.jpg`

## 取得状況

- NotebookLM に新規ノートを作成し、YouTube ソースを追加済み。
- NotebookLM のソース詳細画面から文字起こし本文を確認済み。
- 著作権配慮のため、文字起こし全文はリポジトリへ保存しない。
- YouTubeをブラウザでミュート再生し、動画要素のスクショ取得が可能なことを確認。
- 全秒確認用のフレームは `/tmp` に一時保存し、repo には分析結果だけ残す。

## 見た目の要点

- 16:9の横長白背景。ホワイトボード/紙に手書きしたような濃紺の線が中心。
- オレンジの矢印、黄色の囲み、緑のアクセントで視線誘導する。
- 下部には黒帯字幕が常時入り、白文字でナレーション要点を出す。
- 1枚のスライド内で、枠、見出し、矢印、比較表、吹き出しが順に出る。
- 画面全体のカメラワークより、要素単位の出現順で「次に何が出るか」を作っている。

## 仕組みとして学んだこと

- 動画編集ソフトの作業は、実質的には「要素を塊に分け、順番と出方を決める」作業に分解できる。
- 1スライドごとの順序計画は他スライドと独立しているため、AIエージェントへ並列委譲できる。
- 人間は台本、メッセージ、最終確認へ集中し、キー フレームやイージング選びを直接触らない。
- 下書きはAIが短時間で揃え、最後の字幕、色味、読みやすさ、違和感だけを人間が詰める。

## team-infoへの導入

- 主導入先は `HyperFrames/ai-slide-video-template/`。
- `slide-video-data.js` をAIエージェントの出力先にし、`index.html` の `window.__hf.seek()` がデータからフレーム状態を再計算する。
- 既存の `HyperFrames/tenshoku-short-20260416` と同じく、HTML composition と frame seek を採用する。
- 将来的には `ask-agents-overlay.js` から、選択中スライドのチャンク計画だけをAIへ投げる運用へつなげる。
