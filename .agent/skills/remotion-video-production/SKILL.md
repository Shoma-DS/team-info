---
name: remotion-video-production
description: Remotion動画制作の親スキル。チャンネル選択とテンプレート選択を行い、対応するテンプレート専用スキルを起動して編集フローを実行する。
---

# Remotion動画制作 親スキル

## 目的
- チャンネルとテンプレートを選択し、テンプレート専用スキルへ処理を委譲する。
- テンプレートごとに異なる編集手順を確実に分離する。

## 参照フォルダ
- チャンネル定義ルート: `Remotion/video_resources/channels/`
- 各チャンネル情報: `Remotion/video_resources/channels/<channel_id>/channel_info.md`
- 各テンプレート: `Remotion/video_resources/channels/<channel_id>/templates/*.md`
- テンプレート専用スキル: `.agent/skills/remotion-template-*/`

## 必須フロー
1. `Remotion/video_resources/channels/` のチャンネル一覧を実ディレクトリから取得し、番号付き選択肢で提示して確認する。
2. 選択されたチャンネルの `channel_info.md` を読み込む。
3. `templates/` 内のテンプレート一覧を実ディレクトリから取得し、番号付き選択肢で提示して確認する。
4. 以下のマッピングで、該当するテンプレート専用スキルを起動する。
- `sleep_travel/long_knowledge_relax` -> `remotion-template-sleep-travel-long-knowledge-relax`
- `sleep_travel/short_digest` -> `remotion-template-sleep-travel-short-digest`
5. 親スキル自体はRemotion編集を実行しない。編集は専用スキルでのみ実行する。
6. 専用スキルの実行結果を受け取り、最終報告する。

## 選択肢提示ルール（必須）
- 選択が必要な項目は、推測や固定値ではなく、対象フォルダ内に実在する候補ファイルを列挙して提示する。
- 提示形式は「番号 + ファイル名（必要なら相対パス）」を基本とする。
- 候補が0件の場合は、その場で不足ディレクトリまたは不足拡張子を明示して停止する。
- カスタムエフェクトを新規作成した場合は、都度日本語名を付けてテンプレートとして保存する。

## 新規チャンネル追加ルール
- 新しいチャンネルを作るときは、以下を最低限作成する。
1. `Remotion/video_resources/channels/<channel_id>/channel_info.md`
2. `Remotion/video_resources/channels/<channel_id>/templates/<template_name>.md`（1つ以上）
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
