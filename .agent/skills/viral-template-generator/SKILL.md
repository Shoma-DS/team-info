---
name: viral-template-generator
description: ショート動画の解析、統合分析、台本、字幕、音声、素材、Remotion生成までを扱う入口スキル。テンプレ差分がある場合は template profile を併読して処理する。
---

# viral-template-generator

## 役割
- このスキルはバズ系ショート動画パイプラインの軽い入口として使う
- 詳細手順は `references/flows/` に逃がし、この `SKILL.md` は薄く保つ
- テンプレごとの差分は、そのフェーズで必要なときだけ読む

## このスキルを使う場面
- 参考ショート動画を解析したい
- 分析バッチを統合してパターンをまとめたい
- 台本、字幕、音声、Remotion 組み込みまで進めたい
- 途中フェーズから再開したい
- 解析結果をもとに台本量産用プロンプトテンプレートを作りたい

## 共通パス
- `inputs/viral-analysis/未分析/`
- `inputs/viral-analysis/分析済み/`
- `inputs/viral-analysis/output/`
- `Remotion/my-video/public/viral/`
- `Remotion/my-video/src/viral/`

## コマンドルール
- ユーザーにコマンドを渡すときは `"$TEAM_INFO_ROOT/..."` の絶対パスを使う
- 実行ロジックは `.agent/skills/viral-template-generator/scripts/` を優先する
- 解析やレンダリングのような長時間処理は、必要ならユーザー実行へ切り替える

## 共通 flow
- 概要: `references/pipeline-overview.md`
- 解析: `references/flows/analysis.md`
- 統合分析: `references/flows/patterns.md`
- 台本プロンプトテンプレ生成: `references/flows/prompt-template.md`
- 台本: `references/flows/script.md`
- 字幕・音声: `references/flows/subtitles-voice.md`
- 素材: `references/flows/materials.md`
- Remotion: `references/flows/remotion.md`
- タイミング調整・render: `references/flows/timing.md`

## template profile ルール
1. 可能なら先に template id を確定する
2. `references/template-profiles/[template-id]/profile.yaml` を読む
3. いまのフェーズに対応する override ファイルがあるときだけ追加で読む
4. template が未確定なら `standard-short` を使う

## 再開ルール
- 解析から再開: `analysis.md`
- 統合分析から再開: `patterns.md`
- プロンプトテンプレ生成から再開: `prompt-template.md`
- 台本から再開: `script.md`
- ひらがな、字幕、音声から再開: `subtitles-voice.md`
- 素材から再開: `materials.md`
- Remotion 組み込みから再開: `remotion.md`
- jet cut、alignment、render から再開: `timing.md`

## 差分だけ書くルール
- 共通ロジックは `references/flows/` に置く
- テンプレごとの差分は `references/template-profiles/` に置く
- override ファイルは差分だけを書き、共通 flow を丸ごと重複しない
