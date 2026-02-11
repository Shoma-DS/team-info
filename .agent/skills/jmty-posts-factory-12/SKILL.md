---
name: jmty-posts-factory-12
description: 工場系の案件ファイルを入力にして、ジモティー投稿文を12本作成し、12個の新規フォルダへ分割保存する。
---

# ジモティー 工場求人12本スキル

## 入力ソース
- 案件ファイル置き場: `inputs/jmty_factory_cases/`
- 対象拡張子: `md` `txt` `csv` `json`

## 必須ルール
- 各投稿に `【公式LINEURL】` を必ず入れる。
- 会社名は匿名表現にする（例: 大手製造業、上場グループの工場）。
- 12本で訴求軸・書き出し・対象人物像を重複させない。
- 「注意事項」見出しは入れない。

## 出力
- 出力ルート: `outputs/jmty_posts/factory/<timestamp>/`
- 12フォルダ: `01_post` 〜 `12_post`
- 各フォルダに `post.md`

## 実行フロー
1. `inputs/jmty_factory_cases/` から案件ファイルを選ぶ。
2. `scripts/init_output_dirs.sh` で12フォルダを作る。
3. 案件内容を分解し、工場求人として12本作成して保存する。
4. `【公式LINEURL】` の有無と重複の有無を確認する。
