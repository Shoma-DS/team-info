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
- 素材ごとに出典・ライセンス・検索語を `metadata.json` に残す
- ライセンス不明の画像は自動採用せず、レビュー対象として扱う

## 使えるスクリプト
- `scripts/fetch_materials.py`
- `scripts/upscale_materials.py`

## 素材取得フロー
1. テンプレートを確定し、`profile.yaml` と `phase_refs.materials` を読む
2. `script.md` から hook / section / CTA の素材スロットを作る
3. テンプレートに合う素材取得モードを選ぶ
   - 人物実写: `--template-type person`
   - いらすとや中心: `--template-type irasutoya`
   - 転職・キャリア系: `--template-type career-listicle`
4. `fetch_materials.py` で候補を取得し、`materials/` 直下へ slot 名で配置する
5. `metadata.json` と不足スロットを確認し、ライセンス不明・低解像度・文脈ズレを手動確認する
6. Remotion 側では `00_hook.*`, `02_s1_1.*` のような slot 名をそのまま参照する

## テンプレ差分
- `profile.yaml` を読む
- `phase_refs.materials` があれば追加で読む
- 差分では優先すべき素材の種類を書く
