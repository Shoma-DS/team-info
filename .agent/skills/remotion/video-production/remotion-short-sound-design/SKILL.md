---
name: remotion-short-sound-design
description: Remotionの縦ショート動画に、効果音ラボなどの無料効果音を選定・取得・配置し、字幕/画像/場面転換のテンポと改行品質をテンプレ別基準でチェックする。
---

# Remotion Short Sound Design

## 使う場面
- 縦ショート動画に効果音を追加する。
- テロップ変更や場面転換に合わせて画像や効果音を増やし、テンポを上げる。
- 改行位置、タイトル位置、字幕位置、画像余白をテンプレ別の採点基準でチェックする。
- ユーザーの追加指示をテンプレ別基準へ蓄積し、次回以降の判断に使う。

## 必須フロー
1. 対象 Composition とテンプレートを特定する。
2. テンプレート別基準を読む。縦ショート汎用は `references/templates/viral-short-vertical.md`。
3. 現状 still を代表フレームで取得し、タイトル/画像/字幕/CTA の重なりと余白を見る。
4. 効果音の候補を選ぶ。ビジネス系ショートでは、過剰にゲーム音へ寄せず、短い見出し音・場面転換音・軽い衝撃音を優先する。
5. 効果音を `Remotion/my-video/public/audio/<project>/sfx/` に保存し、用途が分かる英数字名にする。
6. Remotion 側は `sfx` タイムライン配列で管理し、各 `<Sequence>` に `name` を付ける。
7. `npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run typecheck` を実行し、代表 still を再取得して確認する。

## 効果音ラボの取得ルール
- 参照元: `https://soundeffect-lab.info/sound/anime/`
- 直リンク取得は 403 になることがあるため、`curl` では User-Agent と Referer を付ける。

```bash
curl -L -A "Mozilla/5.0" -e "https://soundeffect-lab.info/sound/anime/" \
  "https://soundeffect-lab.info/sound/anime/mp3/news-title1.mp3" \
  -o "$TEAM_INFO_ROOT/Remotion/my-video/public/audio/[project]/sfx/news-title1.mp3"
```

取得後は必ず `file "$TEAM_INFO_ROOT/Remotion/my-video/public/audio/[project]/sfx/*.mp3"` で、HTML ではなく `MPEG ADTS` などの音声ファイルになっているか確認する。

## 選定基準
- フック直後: `ニュースタイトル表示`、`タイトル表示`、`文字表示の衝撃音`。
- 場面転換: `シーン切り替え1/2`。章の開始、CTA への移行に使う。
- 痛み/違和感の強調: `グサッ2`、`ショック2`。多用しない。
- ビジネス・転職系では、コミカルすぎる `間抜け`、過度なホラー、長いファンファーレは原則避ける。
- ナレーションが主役なので、音量は `0.16` から `0.42` 程度で始め、聞き取りを邪魔しない。

## テンポ設計
- 冒頭 0-4 秒は、フックを即表示し、1回は強い視覚/音の切り替えを入れる。
- 章開始時は場面転換音を入れ、タイトルを見せてから本文に入る。
- 字幕が切り替わるタイミングでは、同じ写真を固定し続けず、イラスト/写真/別構図を切り替える。
- 同じ素材を使い回す場合も、字幕ごとにイラストと写真を交互に出して停滞感を減らす。

## テンプレ別基準の更新
- ユーザーが「もっとこうして」と言った内容は、該当テンプレートの基準ファイルへ短く追記する。
- 追記先が不明なら `references/templates/viral-short-vertical.md` に追加し、後で専用テンプレへ分割する。
- 変更前後の still を残し、どの基準を満たすための変更か最終報告に含める。

