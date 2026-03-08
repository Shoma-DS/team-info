---
name: remotion-unified-output-routing
description: 出力先を `outputs/` 配下に統一し、sleep_travel・acoriel・jmty などのカテゴリ別フォルダへ振り分ける運用スキル。レンダリングコマンドや保存場所を案内するときに使い、必ずカテゴリ付きの `outputs/...` を指定する。
---

# Remotion出力先統一スキル

## 絶対パスルール（必須）
- ユーザーにコマンドを渡すときは、固定の `/Users/...` ではなく `TEAM_INFO_ROOT` から絶対パスを組み立てる。
- `cd Remotion/...` や `../../outputs/...` のような相対パスは、ユーザー向けコマンドでは使わない。

## 統一ルール（必須）
- 出力先は常に `outputs/` 配下を使う。
- カテゴリごとに保存先を固定する。
  - Sleep Travel 音声: `outputs/sleep_travel/audio/`
  - Sleep Travel レンダー: `outputs/sleep_travel/renders/`
  - AcoRiel レンダー: `outputs/acoriel/renders/`
  - AcoRiel説明文: `outputs/acoriel/descriptions/`
  - ジモティー: `outputs/jmty/factory/` `outputs/jmty/remote/`
- 旧出力先 `Remotion/output/` `Remotion/renders/` `Remotion/my-video/out/` `Remotion/my-video/outputs/` `outputs/acoriel_descriptions/` は使わない。
- ユーザーが明示的に別パスを指定しない限り、出力コマンドは必ずカテゴリ付き `outputs/...` を指定する。

## コマンド提示ルール（必須）
- Remotionレンダリングの提示は次を優先する。
```bash
bash "$TEAM_INFO_ROOT/Remotion/scripts/render_to_outputs.sh" <CompositionId> <output-file>.mp4
```
- `npx remotion render` を直接提示する場合も、出力先は必ず `"$TEAM_INFO_ROOT/outputs/<channel>/renders/"` にする。
```bash
cd "$TEAM_INFO_ROOT/Remotion/my-video" && npx remotion render "$TEAM_INFO_ROOT/Remotion/my-video/src/index.ts" <CompositionId> "$TEAM_INFO_ROOT/outputs/<channel>/renders/<output-file>.mp4"
```
- VOICEVOX音声生成は `generate_voice.py` を使い、生成結果が `outputs/sleep_travel/audio/` に保存される前提で案内する。

## 問い合わせ対応ルール
- 「どこに出力されたか？」と聞かれたら、まず `outputs/` 配下の該当カテゴリを案内する。
- 旧フォルダにファイルが残っている場合は `outputs/` 配下の適切なカテゴリへ移動して集約する。

## 禁止事項
- 出力パスを省略した `npx remotion render` を提示しない。
- `Remotion/renders/` や `Remotion/output/audio/` を新規保存先として案内しない。
