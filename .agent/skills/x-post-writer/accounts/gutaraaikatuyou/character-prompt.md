# gutaraaikatuyou — キャラクタープロンプト（英語・画像生成用）

このファイルは画像生成AIへのプロンプトに直接組み込む英語説明文です。
`scheduled_draft_pipeline.py` の `build_generation_prompt()` がここを読み込んで
`image_prompt.prompt` 生成指示に自動注入します。

---

## キャラクター説明（画像プロンプトに挿入する英語テキスト）

```
Include a character illustration in the top-right or bottom-right area of the infographic.
Character reference: "Gutara AI CEO" mascot character.
- Hair: black, short, slightly messy and disheveled
- Expression: drowsy, half-lidded eyes, lazy and unmotivated look
- Pose: right cheek resting on right hand, slightly slouching
- Mouth: tongue slightly sticking out, casual and laid-back
- Outfit: dark charcoal suit jacket, red necktie
- Art style: 2D anime / manga illustration style, flat color, clean lines
- Background integration: character blends into the light blue infographic background
- Size: occupies approximately 20-25% of the total image area
- Role: supporting element only — do NOT make the character the focal point
- Do NOT change expression to happy or energetic — keep the lazy, sarcastic vibe
- Do NOT remove the red necktie
- The character's drowsy confidence is a key part of the brand identity
```

---

## 短縮版（スペース節約が必要な場合）

```
Top-right character: Gutara AI CEO — black messy hair, drowsy half-lidded eyes,
cheek on hand, tongue slightly out, dark suit, red necktie, 2D anime style,
lazy but confident expression, 20% image area, supporting role only.
```

---

## キャラクター配置パターン

| パターン | 用途 |
|----------|------|
| 上部右端（縦型上1/3） | 見出しと並列。スペースがある場合 |
| 右下（縦型下1/4） | 結論ブロックの横。吹き出しと組み合わせ可 |
| 吹き出し横 | キャラが結論を言っているように見せる演出 |

---

## NG指定（プロンプトに含める場合）

```
Do NOT make the character smile broadly or look energetic.
Do NOT make the character dominant over the layout.
Do NOT place the character in the center of the image.
Do NOT use a dark or black background behind the character.
```
