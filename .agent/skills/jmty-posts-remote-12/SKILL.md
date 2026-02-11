---
name: jmty-posts-remote-12
description: 在宅系の見本ファイルを入力にして、ジモティー投稿文を12本作成し、12個の新規フォルダへ分割保存する。
---

# ジモティー 在宅求人12本スキル

## 入力ソース
- 見本ファイル置き場: `inputs/jmty_remote_samples/`
- 対象拡張子: `md` `txt` `csv` `json`

## 必須ルール
- 見本を参考にしつつ、12本を別案件に見えるように書き分ける。
- 各投稿に `【公式LINEURL】` を必ず入れる。
- 会社名は匿名表現にする（例: IT系受託企業、全国対応の運用会社）。
- 「注意事項」見出しは入れない。

## 出力
- 出力ルート: `outputs/jmty_posts/remote/<timestamp>/`
- 12フォルダ: `01_post` 〜 `12_post`
- 各フォルダに `post.md`

## 実行フロー
1. `inputs/jmty_remote_samples/` から見本ファイルを選ぶ。
2. `scripts/init_output_dirs.sh` で12フォルダを作る。
3. 在宅系の投稿文を12本作成し、各 `post.md` へ保存する。
4. `【公式LINEURL】` の有無と重複の有無を確認する。
