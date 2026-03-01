# テンプレート: acoustic_cover_multifont_fade_subtitle

## 用途
- AcoRiel向けAIカバーのリリックビデオ制作
- カラオケ追従なし（フェード字幕）で、視認性優先の歌詞表示

## 固定スタイル
1. 字幕演出
- 歌詞字幕は白色グロー
- アニメーションは `FadeInSlow` + `FadeOut` のみ
- カラオケハイライト（単語進行色）は使わない

2. フォント割り当て（文字種別）
- 漢字: `Hachi Maru Pop`
- 英字・数字: `Playwrite NZ Basic`（Google Fonts CSS読み込み）
- ひらがな: `Yosugara`
- カタカナ: `Yosugara`

3. 文字種判定ルール
- `Hiragana` -> ひらがな扱い
- `Katakana` -> ひらがな扱い（Yosugara）
- `Han` -> 漢字扱い
- `[A-Za-z0-9]` -> 英字扱い
- 記号や空白は直前の文字種を引き継ぐ

4. 実装ルール
- テキストは文字種ごとに `span` 分割して `fontFamily` を切り替える
- 単一 `fontFamily` で全文字を描画しない
- イントロ/アウトロ/歌詞字幕を同じフォントルールで統一

## 素材運用
- 音源: `Remotion/my-video/public/assets/channels/acoriel/songs/`
- 背景: `Remotion/my-video/public/assets/channels/acoriel/backgrounds/`
- 効果: `Remotion/my-video/public/assets/channels/acoriel/effects/templates/銀粒子_低刺激リリック.md`
- 歌詞LRC: `Remotion/my-video/public/assets/songs/<曲フォルダ>/lyrics.lrc`（必要に応じて更新）

## 反映先
- `Remotion/my-video/src/AcoRielCover.tsx`
- `Remotion/my-video/src/AcoRielLyricCover.tsx`
- `Remotion/my-video/public/assets/songs/<曲フォルダ>/lyric_animation_data.json`

## 最終チェック
- `npm run lint` を必ず実行
- `npx remotion studio` で `AcoRielLyricCover` を確認
