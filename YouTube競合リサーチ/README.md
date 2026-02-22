# YouTube競合リサーチ（Apps Script）

競合用スプレッドシートに、登録チャンネルの人気動画を自動で追記するスクリプトです。

## 対象スプレッドシート

- [Youtubeデータリサーチ（AIカバー）](https://docs.google.com/spreadsheets/d/1XTfZOQ3IFHU9uhgRmc3TF4Jk-YHe7FS8fS7BzvJPshc/edit?usp=sharing) … `YouTubeCompetitorResearch.gs`
- [Youtubeデータリサーチ（睡眠朗読）](https://docs.google.com/spreadsheets/d/1rlna35UZiTnTT9G4xRl1AKM6AGcaRhmS_5OUtfSAtnM/edit?usp=sharing) … `YouTubeCompetitorResearch_睡眠朗読.gs`

## セットアップ

1. **対象スプレッドシートを開く**
2. **拡張機能** → **Apps Script** でエディタを開く
3. デフォルトの `Code.gs` を削除し、対応する `.gs` ファイルの内容を貼り付けて保存
4. **高度な Google サービス** で **YouTube Data API v3**（サービスID: `YouTube`）を有効化
5. GCP プロジェクトで **YouTube Data API v3** を有効化

## スプレッドシート上部のボタン

メニュー **YouTubeリサーチ** → **YouTubeリサーチボタンを設置** を実行すると、1行目に「項目ヘルプ」「YouTubeリサーチ」の列が追加され、2行目にドロップダウンボタンが表示されます。ドロップダウンから操作を選択すると、対応するリサーチが実行されます。

**リサーチパネルを開く** を選択すると、サイドバーに3つのボタンが表示され、クリックでリサーチを実行できます。

## タブ

- **Youtube動画** … 取得した動画が追記されるタブ。なければ自動作成され、1行目にヘッダーが入ります。
- **Youtubeチャンネル** … 調査対象チャンネル一覧。次のいずれかの列が必要です。
  - チャンネルID または チャンネルURL  
  任意で「再生数」列があると、その値でチャンネルをソートしてから処理します（なければ API で取得してソート）。

## 実行

Apps Script エディタで `runCompetitorYouTubeResearch` を選択して「実行」するか、スプレッドシートのメニューやトリガーから呼び出してください。

## 注意

- 競合チャンネルは Analytics API が使えないため、離脱率・保持率・平均視聴率は取得しません。
- 1チャンネルあたり最大50本まで取得（`CONFIG.MAX_VIDEOS_PER_CHANNEL` で変更可）。
