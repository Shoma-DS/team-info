# Remotion動画制作スキル マニュアル

## 概要
このスキルは、Remotionでの動画制作をチャンネル別テンプレートで標準化するための親スキルです。

固定フロー:
1. チャンネル選択
2. テンプレート選択
3. テンプレート専用スキル起動
4. Remotion編集

## 参照先
- チャンネル定義: `Remotion/my-video/public/assets/channels/`
- Remotion本体: `Remotion/my-video/`
- テンプレート専用スキル:
  - `.agent/skills/remotion/remotion-template-sleep-travel-long-knowledge-relax/SKILL.md`
  - `.agent/skills/remotion/remotion-template-sleep-travel-short-digest/SKILL.md`
  - `.agent/skills/acoriel/remotion-template-acoriel-acoustic-cover/SKILL.md`

## 使い方
1. 「Remotionで動画を作って」などの依頼を出す
2. チャンネルを選ぶ
3. テンプレートを選ぶ
4. 発動したテンプレート専用スキルの編集結果を確認する

## テンプレート設計の基本
- 動画尺
- シーン構成
- テキスト/CTA
- デザイン方針
- 編集チェックリスト

## 運用ルール
- チャンネルごとにフォルダを分ける
- テンプレートはチャンネル配下の `templates/` に置く
- 新規チャンネル追加時は `channel_info.md` を必ず作る
- 新規テンプレート追加時は、テンプレート専用スキルを作成する
