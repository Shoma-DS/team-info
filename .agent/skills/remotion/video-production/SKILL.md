---
name: remotion-video-production
description: Remotion動画制作の親スキル。チャンネル選択とテンプレート選択を行い、対応するテンプレート専用スキルを起動して編集フローを実行する。
---

# Remotion動画制作 親スキル

## 絶対パスルール（必須）
- ユーザーにコマンドを渡すときは、固定の `/Users/...` ではなく `TEAM_INFO_ROOT` から絶対パスを組み立てる。
- レンダリングコマンドを見せるときは、出力先も `"$TEAM_INFO_ROOT/outputs/..."` にする。

## 目的
- チャンネルとテンプレートを選択し、テンプレート専用スキルへ処理を委譲する。
- テンプレートごとに異なる編集手順を確実に分離する。

## メディアレイヤー統合ルール（全Remotion共通・必須）
- 同じファイル種類（画像・動画・音声・字幕など）で、表示または再生区間が互いに重ならない素材は、原則その種類ごとに `<Sequence>` を1本へ統合する。
- `items.map(...<Sequence>...)` のように、非重複な同種素材を個別の `<Sequence>` へ並べる実装は禁止する。
- 基本実装は「`<Sequence>` 1本 + タイムライン配列 + 現在フレームからアクティブ素材を選択して描画」とする。
- 複数 `<Sequence>` を許可するのは、同種素材が同時表示/同時再生される場合、独立レイヤー合成が必要な場合、クロスフェードなど意図的な時間重複がある場合のみとする。
- 既存実装がこの原則に反している場合、新しい演出や素材追加の前に、まず同種レイヤーの1本化を検討する。
- 生成・更新する **すべての `<Sequence>` に `name` を付ける。** `背景画像`、`字幕`、`音声 ナレーション` のように役割が即分かる名前にし、`Layer1` のような曖昧名は使わない。

## 参照フォルダ
- チャンネル定義ルート: `Remotion/my-video/public/assets/channels/`
- 各チャンネル情報: `Remotion/my-video/public/assets/channels/<channel_id>/channel_info.md`
- 各テンプレート: `Remotion/my-video/public/assets/channels/<channel_id>/templates/*.md`
- テンプレート専用スキル:
  - `.agent/skills/remotion/remotion-template-*/`（sleep_travel系）
  - `.agent/skills/acoriel/remotion-template-*/`（acoriel系）

## 必須フロー
1. `Remotion/my-video/public/assets/channels/` のチャンネル一覧を実ディレクトリから取得し、番号付き選択肢で提示して確認する。
2. 選択されたチャンネルの `channel_info.md` を読み込む。
3. `templates/` 内のテンプレート一覧を実ディレクトリから取得し、番号付き選択肢で提示して確認する。
4. 以下のマッピングで、該当するテンプレート専用スキルを起動する。
- `sleep_travel/long_knowledge_relax` -> `remotion-template-sleep-travel-long-knowledge-relax` (./remotion-template-sleep-travel-long-knowledge-relax/SKILL.md)
- `sleep_travel/short_digest` -> `remotion-template-sleep-travel-short-digest` (./remotion-template-sleep-travel-short-digest/SKILL.md)
- `acoriel/acoustic_cover` -> `remotion-template-acoriel-acoustic-cover` (./acoriel/remotion-template-acoriel-acoustic-cover/SKILL.md)
5. 親スキル自体はRemotion編集を実行しない。編集は専用スキルでのみ実行する。
6. 専用スキルの実行結果を受け取り、最終報告する。

## 選択肢提示ルール（必須）
- 選択が必要な項目は、推測や固定値ではなく、対象フォルダ内に実在する候補ファイルを列挙して提示する。
- 提示形式は「番号 + ファイル名（必要なら相対パス）」を基本とする。
- 候補が0件の場合は、その場で不足ディレクトリまたは不足拡張子を明示して停止する。
- カスタムエフェクトを新規作成した場合は、都度日本語名を付けてテンプレートとして保存する。

## 新規チャンネル追加ルール
- 新しいチャンネルを作るときは、以下を最低限作成する。
1. `Remotion/my-video/public/assets/channels/<channel_id>/channel_info.md`
2. `Remotion/my-video/public/assets/channels/<channel_id>/templates/<template_name>.md`（1つ以上）
- `channel_info.md` に含める項目:
- チャンネル名
- 想定視聴者
- 禁止事項
- トーン&マナー
- デザインガイド（色/フォント方針）
- CTAルール
- テンプレート追加時は、同名のテンプレート専用スキルを新規作成する。

## 失敗時の扱い
- テンプレート未選択、または定義ファイル不足の場合は編集を開始せず、不足ファイル名を明示して止める。
- 専用スキルが未作成の場合は、必要なスキル名を明示して作成を促す。

## レンダリング確認ルール（必須）
- `cd "$TEAM_INFO_ROOT/Remotion/my-video" && npx remotion render ...` は、ユーザーの明示承認があるまで実行しない。
- レンダリング前は必ず次の文言で確認する:
  - `出力しますか？書き出しますか？`
- 既に過去ターンで承認済みでも、**毎回**レンダリング直前に再確認する。
- 承認がない場合は、実行せずにコピペ可能なレンダリングコマンドのみ提示する。
- レンダリング出力先は必ず `outputs/<channel>/renders/` を使う。
