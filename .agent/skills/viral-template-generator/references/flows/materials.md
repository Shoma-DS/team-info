# materials

## 目的
- 必要素材数を決めて `materials/README.md` を整える
- 収集ルールをテンプレ方針と揃える

## 標準出力
- `materials/README.md`
- A slot list for each scene group or section

## 標準ルール
- `viral_patterns.md` から最低限必要な素材数を見積もる
- 必須スロットと任意スロットを分ける
- ユーザーがすぐ動ける収集ルールを優先する
- Remotion 側で扱いやすい命名規則にする

## 使えるスクリプト
- `scripts/fetch_materials.py`
- `scripts/upscale_materials.py`

## テンプレ差分
- `profile.yaml` を読む
- `phase_refs.materials` があれば追加で読む
- 差分では優先すべき素材の種類を書く
