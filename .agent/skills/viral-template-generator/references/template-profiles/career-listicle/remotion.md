# career-listicle / remotion 差分

## 共通 flow からの変更
- 強いカメラワークより static や gentle を優先する
- シーン切り替えは画像クロスフェードを基本にする
- flash や shake は、分析根拠が強い場合だけ使う
- 劇的な盛り上げより、情報整理しやすい一定テンポを狙う
- `fetch_materials.py --template-type career-listicle` で配置した slot 画像を優先して使う
- 画像が揃っている場合は、既存素材を使い回す前に `00_hook.*`, `02_s1_1.*`, `03_s2_1.*`, `04_s3_1.*`, `99_cta.*` を Remotion の `visuals` に組み込む
- 素材が不足した slot だけ既存画像や手動素材で補完する
