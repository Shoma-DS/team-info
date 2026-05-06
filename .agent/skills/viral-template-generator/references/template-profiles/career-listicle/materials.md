# career-listicle / materials 差分

## 共通 flow からの変更
- ビジネス、面接、履歴書、職場、意思決定のイメージを優先する
- 同じ人物を追うより、論点ごとの切り替えを重視する
- 説明が早く伝わるなら汎用ストック素材も使ってよい
- 転職ショートでは、明示指示がない限り `fetch_materials.py --template-type career-listicle` を使う
- 画像ソースの優先順位は `いらすとや` → `Openverse / Wikimedia Commons` → 手動配置
- いらすとや素材は、各セクションの論点に合う検索語で取得する
  - 例: `出社 疲れ`, `相談 上司`, `残業`, `キャリアアップ`, `転職`
- フックは `転職`, `会社員 悩む`, `仕事 疲れ` のように一目で転職文脈が伝わるものを優先する
- CTA は `保存`, `チェック`, `転職活動`, `未来` のように行動を促す画像を優先する
- 取得後は `metadata.json` を確認し、利用規約・点数制限・クレジット要否を人間が最終確認する

## 推奨コマンド

```bash
python "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/fetch_materials.py" \
  --materials-dir "$TEAM_INFO_ROOT/Remotion/my-video/public/viral/[動画フォルダ]" \
  --script "$TEAM_INFO_ROOT/[script.md]" \
  --template-type career-listicle \
  --candidates-per-person 4
```

## Remotion 配置
- `00_hook.*`: 冒頭フック
- `02_s1_1.*` から `02_s1_3.*`: セクション1
- `03_s2_1.*` から `03_s2_3.*`: セクション2
- `04_s3_1.*` から `04_s3_3.*`: セクション3
- `99_cta.*`: CTA
