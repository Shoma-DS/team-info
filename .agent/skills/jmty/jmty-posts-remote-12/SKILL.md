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
- 12本すべてで「未経験OK（未経験歓迎）」を明記する。
- 各投稿に `【公式LINEURL】` を必ず入れる。
- 会社名は匿名表現にする（例: IT系受託企業、全国対応の運用会社）。
- 「注意事項」見出しは入れない。
- 投稿の順序・見出し・口調・語尾・絵文字有無を固定化しない。

## テンプレート運用
- テンプレート置き場: `.agent/skills/jmty/jmty-posts-remote-12/assets/post_templates/`
- `template01`〜`template12` を1投稿につき1つずつ割り当てる。
- 各テンプレートで構成順が異なるため、投稿間で見た目が似ないようにする。

## 出力
- 出力ルート: `outputs/jmty/remote/<timestamp>/`
- 12ファイルを直下に出力: `post01.md` 〜 `post12.md`

## 実行フロー
1. `inputs/jmty_remote_samples/` から見本ファイルを選ぶ。
2. `.agent/skills/jmty/jmty-posts-remote-12/scripts/init_output_dirs.py` で `post01.md` 〜 `post12.md` を作る。
3. `.agent/skills/jmty/jmty-posts-remote-12/assets/post_templates/` の12テンプレを1本ずつ割り当てる。
4. 在宅系の投稿文を12本作成し、各 `postNN.md` へ保存する。
5. 次を確認する。
- 全投稿に `未経験OK` がある
- 全投稿に `【公式LINEURL】` がある
- 書き方・順序・口調が重複していない
