## Slash Commands

ユーザーが `/コマンド名` を入力したときは、対応するスキルを即座に読み込んで動作すること。

| コマンド | 読み込むスキル |
|---------|--------------|
| `/acoriel` | `.agent/skills/acoriel/remotion-template-acoriel-acoustic-cover/SKILL.md` |
| `/git` | `.agent/skills/common/git-workflow/SKILL.md` → コミット＋プッシュ |
| `/setup` | `.agent/skills/common/team-info-setup/SKILL.md` |
| `/sleep-travel` | `.agent/skills/remotion/remotion-video-production/SKILL.md` |
| `/lyric` | `.agent/skills/remotion/lyric-emotion-mapper/SKILL.md` |
| `/voice` | `.agent/skills/remotion/voice-script-launcher/SKILL.md` |
| `/jmty` | `.agent/skills/jmty/jmty-posts/SKILL.md` |
| `/script` | `.agent/skills/remotion/script-writing-accounts-aware/SKILL.md` |

## Skills
A skill is a set of local instructions stored in a `SKILL.md` file.
From now on, this repository uses only `.agent/skills` as the skills source.

## Canonical Agent File
- このリポジトリのエージェント向け指示の正本は `AGENTS.md` とする。
- `Agent.md` は互換用の案内ファイルとして扱い、内容の更新は原則 `AGENTS.md` のみで行う。
- フォルダ命名規則・禁止事項・用途マップは `RULES.md` を参照すること。
- 各サブフォルダの `CLAUDE.md` にそのフォルダの詳細文脈が記載されている。

## Behavior Principles
- ユーザーの意図と目的を正確に理解する。不明点が重要なら確認する。
- 安全性を優先しつつ、タスクは効率的に遂行する。
- 既存のコード規約、アーキテクチャ、スタイルを尊重する。
- 要求タスクだけでなく、必要な付随作業や品質改善も実施または提案する。
- 重要な変更やコマンド実行の前には、目的と影響を簡潔に説明する。
- 明確な範囲を超える変更や影響の大きい変更は、必ずユーザー確認を取る。
- ユーザーとの対話は原則日本語で行う。
- ユーザーが明示しない限り `.gitignore` は変更しない。必要なら事前に許可を取る。
- Git関連操作を行う場合は、必ず `.agent/skills/common/git-workflow/SKILL.md` を使う。

## Command Path Rules
- ユーザーにコマンドを渡すときは、**必ず絶対パス**で書く。
- 固定の `/Users/...` は使わず、`TEAM_INFO_ROOT` から絶対パスを組み立てる。
- `TEAM_INFO_ROOT` は、このリポジトリのチェックアウト先を指す各パソコンごとの環境変数とする。
- 新しいパソコンでは、まず `setup/setup_all.cmd` の流れを優先する。
- `setup-local-machine` は、`TEAM_INFO_ROOT` の保存だけをやり直したいときの手動補助として使う。
- このパソコンをオーナー機として使う場合だけ、`setup-local-machine` に `--owner` を付ける。
- `cd Remotion/...` や `python .agent/...` のような相対パスのコマンドは、ユーザー向けには渡さない。
- リポジトリ内コマンドは、できるだけ次の形で渡す。
  - Git: `git -C "$TEAM_INFO_ROOT" ...`
  - npm: `npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" ...`
  - リポジトリ内Python: `python "$TEAM_INFO_ROOT/..."`
  - Docker 起動: `bash "$TEAM_INFO_ROOT/run.sh" --project [n8n|dify] ...`
  - Windows の Docker 起動: `& "$env:TEAM_INFO_ROOT\\run.ps1" -Project [n8n|dify] ...`
- ユーザー指定の入力/出力パスが入る場合も、`"$TEAM_INFO_ROOT/..."` や `"[出力先の絶対パス]"` のように絶対パス前提で案内する。

## New Machine Rule
- 作業開始時は、まず `team_info_runtime.py worked-before-status` 相当で、そのパソコンが過去に `team-info` で作業したことがあるかを確認する。
- 判定にはローカル設定ディレクトリの `worked_before_machines.json` を使う。
- 結果が `known` なら、通常どおり作業を進めてよい。
- 結果が `new` なら、最初に `マニュアル/まずはこちらをお読みください.md` を読み込み、その流れに沿ってセットアップを始める。
- `setup-local-machine` や `setup/setup_all.cmd` が終わったら、このパソコンは自動で `worked_before_machines.json` に記録される前提で扱う。
- 新しいパソコンでのセットアップが終わったら、ユーザーへもう一度 `マニュアル/まずはこちらをお読みください.md` を読むように促す。
- それでもユーザーがわからない場合は、止まった画面のスクリーンショットを添えて次の Discord へ質問するよう案内する。
- Discord 案内先: `https://discord.com/channels/1478351976168165511/1479287635535990794`

### Available skills

スキルは `.agent/skills/` 配下のフォルダで管理しています。
タスクに該当するスキルが不明な場合は **skill-finder** スキル (`.agent/skills/skill-finder/SKILL.md`) を起動して特定してください。

フォルダ構成:
- `acoriel/`                   — アコリエルチャンネル（リリックビデオ・概要欄）
- `remotion/`                  — Remotion動画制作（寝ながらトラベル・台本・音声）
- `jmty/`                      — ジモティー投稿
- `common/`                    — 共通ユーティリティ（Git・note記事・macOS互換）
- `web-design/`                — Webフロントエンド（GSAP・UI制作）
- `canva/`                     — Canva連携
- `viral-template-generator/`  — バズ動画テンプレ自動生成
- `skill-finder/`              — スキル検索（上記から最適スキルを特定）

### Skill maintenance rules
- 新しいスキルを `.agent/skills/` に追加したときは、**必ず** `.agent/skills/skill-finder/SKILL.md` のスキル一覧とガイドを更新すること。
- 既存スキルの概要・パスが変わったときも同様に更新すること。

### How to use skills
- Discovery: Open the relevant `SKILL.md` and read only what is needed for the current task.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text), use that skill in the same turn.
- Path resolution: Resolve relative paths from each skill directory first.
- Reuse first: Prefer scripts/templates/assets inside the skill over recreating artifacts.
- Coordination: If multiple skills apply, use the minimal set and state the order briefly.
- Fallback: If a skill is missing or unclear, state the issue briefly and continue with the best practical approach.

### Tool Execution Security Rules

**このルールは Claude・Codex・Gemini など、すべての AI エージェントに適用される。**

- ツール実行（Bash、ファイル操作など）の許可を求めるときは、必ず日本語で説明・確認を行うこと
- 許可を求める際、以下のセキュリティリスクをパーセンテージ(%)で提示すること
  - パスワードや秘密鍵が外に漏れる可能性
  - 外部サーバーにデータが送られる可能性
  - 悪意あるコードが勝手に動く可能性
  - PCの設定が書き換わる可能性

以下の**すべて**を満たす場合は、ユーザーに確認せず**自動で実行してよい**:

- 上記リスクがすべて **5% 以下**
- **ファイル・フォルダの削除**を行わない
- **システム設定・環境変数の永続的な変更**を行わない
- **外部へのデータ送信**（API呼び出し・curl・wget等）を行わない

上記のいずれかに該当する場合のみ、リスクを提示してユーザーに確認を取ること。
それ以外（危険性が極端に低い通常作業）は確認なしで進めてよい。

### Approval and Selection Rules
- 承認が必要な操作は、必ずこのチャット上でユーザーに承認を求めてから進める。
- ユーザーに選択肢や確認応答を求める場合は、質問を出す直前に必ず通知を鳴らす。
- 通知付きの選択フローをスクリプト化する場合も、通知を先に鳴らしてから入力待ちに入る。
- Git の push 判断でオーナー確認が必要なときは、ユーザーへ立場を聞かず、`team_info_runtime.py owner-status` の結果で機械側を判定して進める。
