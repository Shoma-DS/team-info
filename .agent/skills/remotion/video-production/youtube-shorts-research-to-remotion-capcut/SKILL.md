---
name: youtube-shorts-research-to-remotion-capcut
description: GoogleスプレッドシートのYouTube競合動画リサーチ結果を分析し、勝ちパターンを抽出して、同じ方向性の縦型ShortsをRemotionで自動生成し、CapCutで仕上げ編集するためのコンテキストと編集指示を作る。
---

# youtube-shorts-research-to-remotion-capcut

## 目的
Google Sheets の `競合動画リサーチ` / `競合チャンネル` を読み、伸びているShortsの型を分析して、Remotion生成とCapCut仕上げへ渡せる制作コンテキストに変換する。

このスキルは、ユーザーが次のように依頼したときに使う。
- スプレッドシートのYouTube競合リサーチを分析したい
- 競合と同じようなShortsを作りたい
- RemotionからCapCutへ渡す自動編集フローを作りたい
- 競合動画データから動画テンプレ、台本、編集JSONを作りたい

## 入力
- Google Sheets URL
- 対象シート名。未指定なら `競合動画リサーチ` と `競合チャンネル`
- 作りたい動画ジャンル、禁止表現、素材方針
- 任意: 参考にする上位動画本数、尺、投稿先

## 基本ワークフロー
1. `gws sheets spreadsheets get` でシート一覧と `gid` を確認する。
2. `競合動画リサーチ` のヘッダーとデータを読む。
3. `競合チャンネル` からチャンネル名、登録者数、投稿本数、概要欄を読む。
4. 再生数、尺、高評価、コメント、タイトル語尾、テーマを集計する。
5. 伸びている型を `制作コンテキスト` として要約する。
6. Remotion用に、尺、シーン割り、字幕、素材スロット、効果音ポイントを設計する。
7. CapCut用に、BGM、字幕、ズーム、カット、効果音、書き出し指示をJSONまたはMarkdownで出す。
8. 生成物がある場合は `outputs/youtube-shorts-research/` に置き、Google Driveへのコピー手順を案内する。

## 分析観点
- 動画本数、平均再生数、最大/最小再生数
- 平均尺。Shortsでは30-55秒を優先し、勝ち筋があるなら38-43秒を標準にする
- タイトルの型
  - `〇〇さん、ついに見つかるw`
  - `〇〇、あまりにも逸材すぎると話題にw`
  - `【悲報】〇〇さん、またやらかしてしまうw`
  - `〇〇さん、最高すぎると話題にw`
- テーマ分類
  - 発見型
  - 悲報/やらかし型
  - 逸材/最高型
  - ネット話題型
- コメントされやすい論点
- 概要欄や引用元の有無
- 権利リスク。競合の映像、画像、字幕、構成をそのままコピーしない

## Remotion設計
標準は 9:16 / 1080x1920 / 30fps / 36-45秒。

出力する構成:
- `projectContext`: チャンネル、競合、狙う視聴者、禁止事項
- `videoBrief`: タイトル案、尺、フック、オチ
- `scenePlan`: 2-4秒単位のシーン配列
- `assetPlan`: 背景素材、人物素材、引用テキスト、差し替え枠
- `captionPlan`: 大字幕、強調語、改行位置
- `soundPlan`: BGM、効果音、無音ポイント
- `capcutInstructions`: CapCutで仕上げる操作

## 推奨テンプレ
```text
0-3秒: 強い導入
3-10秒: 誰が何で話題か
10-25秒: 見どころを2-4秒ごとに連打
25-35秒: コメントされやすい論点
35-42秒: オチ、軽い一言、余韻
```

## CapCut受け渡し
CapCutへ渡す編集指示は、Remotionで作った仮動画を前提に次を明記する。
- 自動字幕の有無
- BGM候補と音量
- 効果音タイミング
- ズーム/パン/揺れ
- テロップ強調語
- 画像や動画素材の差し替え箇所
- 書き出し設定

## 既存コンテキスト例
`新Youtubeデータリサーチ（アダルト）` の分析では、以下の型を確認済み。
- チャンネル: `ムクムク速報【ムク速】`
- Shorts 20本
- 平均再生数: 約212万
- 最大再生数: 約325万
- 平均尺: 約41秒
- 勝ち筋: 人物発見、話題化、軽い煽り、タイトル末尾の `w`

## 成果物
必要に応じて次を作る。
- `context.md`: 分析結果と制作方針
- `brief.json`: Remotion/CapCut共通の制作コンテキスト
- `script.md`: ナレーション台本
- `capcut-instructions.json`: CapCut仕上げ指示

## Google Drive コピー
生成物を作った場合、出力先は原則:

```bash
$TEAM_INFO_ROOT/outputs/youtube-shorts-research/
```

Google Driveへコピーする場合は、ユーザーに次のコマンドを提示する。エージェントが勝手に実行しない。

```bash
rclone copy "$TEAM_INFO_ROOT/outputs/youtube-shorts-research/" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/youtube-shorts-research/" --progress
```

rclone が未設定の場合は `.agent/skills/common/git-workflow/gdrive-copy/SKILL.md` の初回セットアップ手順を案内する。
