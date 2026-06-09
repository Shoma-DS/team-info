---
name: youtube-shorts-style-video-maker
description: YouTube競合リサーチ分析済みの制作コンテキスト、brief.json、script.md、capcut-instructions.json などを入力にして、同じ様式の縦型ShortsをRemotionで制作し、CapCut仕上げパッケージまで作る。スプレッドシート分析は不要で、既に抽出された勝ちパターンから動画を作るだけのときに使う。
---

# youtube-shorts-style-video-maker

## 目的
`youtube-shorts-research-to-remotion-capcut` で作った分析結果を、実際の縦型ショート動画へ落とし込む。

このスキルは分析をやり直さない。既存の `context.md` / `brief.json` / `script.md` / `capcut-instructions.json` などから、同じ様式の新作Shortsを作る。

## 入力
- 分析済み制作コンテキストの保存先
  - `outputs/youtube-shorts-research/context.md`
  - `outputs/youtube-shorts-research/brief.json`
  - `outputs/youtube-shorts-research/script.md`
  - `outputs/youtube-shorts-research/capcut-instructions.json`
- 新作動画のテーマ、扱う人物・商品・ニュース・ネタ
- 禁止表現、権利面の注意、使ってよい素材範囲
- 任意: 尺、投稿先、タイトル案、ナレーション音声

## 最初に読むもの
1. `.agent/skills/remotion/video-production/SKILL.md`
   - Remotion共通ルール、画像素材ルール、CapCut同期ルール、レンダリング確認ルールを守る。
2. 入力として渡された分析済みファイル
   - `brief.json` がある場合は最優先で構造を読む。
   - `context.md` は勝ちパターンと禁止事項の確認に使う。
   - `script.md` は台本の初稿として使う。
   - `capcut-instructions.json` は仕上げ編集の正本として使う。

## 基本ワークフロー
1. 分析済みファイルを読み、勝ちパターンを短く要約する。
2. 今回作る新作テーマを、その勝ちパターンへ当てはめる。
3. 台本を必要最小限だけ調整し、既存動画や競合動画の字幕・映像・画像をそのままコピーしない。
4. 9:16 / 1080x1920 / 30fps のRemotion縦ショートとして、Compositionまたは既存 `ViralTemplate` 系データを更新する。
5. 台本ごとに新規の背景画像、挿絵、写真素材の計画を作る。過去ショート素材の流用は禁止する。
6. 字幕、強調語、カット、ズーム、効果音ポイントを分析済みの様式に合わせる。
7. lint/typecheck を実行できる範囲で確認する。
8. Composition更新後は `sync:capcut` を実行し、CapCut用パッケージ生成結果を報告する。
9. レンダリングが必要な場合は、必ずユーザーに `出力しますか？書き出しますか？` と確認してから行う。

## 制作方針
- 競合の勝ちパターンは「型」として使い、映像・画像・字幕文言・固有の構成はコピーしない。
- 標準尺は分析結果に従う。未指定なら 36-45秒、話題系Shortsなら 38-43秒を目安にする。
- 冒頭3秒で「誰が何で話題か」を即提示する。
- 2-4秒単位で画面変化、字幕強調、ズーム、効果音を入れる。
- コメントされやすい論点を終盤に置く。
- オチは軽く、余韻を残して終える。

## Remotion実装ルール
- 既存の `ViralTemplate` 系Compositionが使える場合は、まずそれに合わせる。
- 新規Compositionを作る場合は、ファイル冒頭に「何をするコードか」の説明コメントを入れる。
- 同じ種類の非重複素材は、Remotion親スキルのメディアレイヤー統合ルールに従い、可能な限り1本の `<Sequence>` とタイムライン配列で扱う。
- すべての `<Sequence>` に役割が分かる `name` を付ける。
- 素材パスは動画ごとの専用フォルダを使う。
- 過去作素材への参照が残っていないか、最後に `rg` で確認する。

## CapCut受け渡し
Remotion更新後、次を実行する。

```powershell
npm --prefix "$env:TEAM_INFO_ROOT\Remotion\my-video" run sync:capcut
```

`cutcli` 未導入でドラフト生成がスキップされた場合は失敗扱いにしない。`outputs/capcut/` のパッケージ生成状況を報告する。

## 成果物
必要に応じて次を作る。
- Remotion Composition / data / asset files
- `outputs/youtube-shorts-research/style-video-brief.json`
- `outputs/youtube-shorts-research/style-video-script.md`
- `outputs/youtube-shorts-research/style-video-capcut-notes.md`
- `outputs/capcut/` 配下のCapCut連携パッケージ

## Google Drive コピー
生成物を作った場合、Google Driveへコピーするにはユーザーに次のコマンドを提示する。エージェントが勝手に実行しない。

```bash
rclone copy "$TEAM_INFO_ROOT/outputs/youtube-shorts-research/" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/youtube-shorts-research/" --progress
```

rclone が未設定の場合は `.agent/skills/common/git-workflow/gdrive-copy/SKILL.md` の初回セットアップ手順を案内する。

