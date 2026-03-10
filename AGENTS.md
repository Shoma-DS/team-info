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
- 新しいパソコンでは、リポジトリルートで `python .agent/skills/common/scripts/team_info_runtime.py setup-local-machine --repo-root .` を 1 回実行して保存する。
- このパソコンをオーナー機として使う場合だけ、上のコマンドに `--owner` を付ける。
- `cd Remotion/...` や `python .agent/...` のような相対パスのコマンドは、ユーザー向けには渡さない。
- リポジトリ内コマンドは、できるだけ次の形で渡す。
  - Git: `git -C "$TEAM_INFO_ROOT" ...`
  - npm: `npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" ...`
  - リポジトリ内Python: `python "$TEAM_INFO_ROOT/..."`
- ユーザー指定の入力/出力パスが入る場合も、`"$TEAM_INFO_ROOT/..."` や `"[出力先の絶対パス]"` のように絶対パス前提で案内する。

### Available skills
- acoriel-video-description: Acoriel（アコリエル）チャンネルのYouTube動画概要欄を生成する。 (file: .agent/skills/acoriel/acoriel-video-description/SKILL.md)
- remotion-template-acoriel-acoustic-cover: acoriel向けのアコースティックカバー用Remotion編集。 (file: .agent/skills/acoriel/remotion-template-acoriel-acoustic-cover/SKILL.md)
- remotion-video-production: Remotion動画制作の親スキル（チャンネル/テンプレ選択）。 (file: .agent/skills/remotion/remotion-video-production/SKILL.md)
- remotion-template-sleep-travel-long-knowledge-relax: sleep_travel長尺動画テンプレ編集。 (file: .agent/skills/remotion/remotion-template-sleep-travel-long-knowledge-relax/SKILL.md)
- remotion-template-sleep-travel-short-digest: sleep_travel短尺動画テンプレ編集。 (file: .agent/skills/remotion/remotion-template-sleep-travel-short-digest/SKILL.md)
- lyric-video-production: 音声と歌詞からLRC生成とリリック演出を行う。 (file: .agent/skills/remotion/lyric-emotion-mapper/SKILL.md)
- script-writing-accounts-aware: アカウント連動の段階的な台本作成。 (file: .agent/skills/remotion/script-writing-accounts-aware/SKILL.md)
- voice-script-launcher: 台本をVOICEVOXで音声化する実行フロー。 (file: .agent/skills/remotion/voice-script-launcher/SKILL.md)
- remotion-unified-output-routing: 出力先を `outputs/` 配下へ統一する運用。 (file: .agent/skills/remotion/remotion-unified-output-routing/SKILL.md)
- jmty-posts: ジモティー投稿作成の親スキル。 (file: .agent/skills/jmty/jmty-posts/SKILL.md)
- jmty-posts-factory-12: 工場求人向け投稿文を12本作成する。 (file: .agent/skills/jmty/jmty-posts-factory-12/SKILL.md)
- jmty-posts-remote-12: 在宅求人向け投稿文を12本作成する。 (file: .agent/skills/jmty/jmty-posts-remote-12/SKILL.md)
- jmty-posts-12-variants: 案件ファイルから12本の投稿文を作成する。 (file: .agent/skills/jmty/jmty-posts-12-variants/SKILL.md)
- jmty-posts-gdrive-sync: ジモティー投稿出力をGoogleドライブに同期する。 (file: .agent/skills/jmty/jmty-posts-gdrive-sync/SKILL.md)
- git-workflow: Gitの安全なブランチ/コミット/プッシュ手順。 (file: .agent/skills/common/git-workflow/SKILL.md)
- macos-intel-compatibility: Intel MacのPython/PyTorch互換性対応。 (file: .agent/skills/common/macos-intel-compatibility/SKILL.md)
- note-article-ayumi: 「愛され女子あゆみ」のnote記事を作成する。 (file: .agent/skills/common/note-article-ayumi/SKILL.md)
- frontend-design: 高品質なフロントエンドUIを制作する。 (file: .agent/skills/web-design/frontend-design/SKILL.md)
- gsap-awwwards-website: GSAPスクロール演出付きLPを開発/保守する。 (file: .agent/skills/web-design/gsap-awwwards-website/SKILL.md)
- skill-finder: タスクに合うスキルを一覧から特定する。 (file: .agent/skills/skill-finder/SKILL.md)
- viral-template-generator: ショート動画を3層解析しRemotionバズ動画テンプレートを自動生成する。 (file: .agent/skills/viral-template-generator/SKILL.md)

### How to use skills
- Discovery: Open the relevant `SKILL.md` and read only what is needed for the current task.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text), use that skill in the same turn.
- Path resolution: Resolve relative paths from each skill directory first.
- Reuse first: Prefer scripts/templates/assets inside the skill over recreating artifacts.
- Coordination: If multiple skills apply, use the minimal set and state the order briefly.
- Fallback: If a skill is missing or unclear, state the issue briefly and continue with the best practical approach.

### Tool Execution Security Rules

- ツール実行（Bash、ファイル操作など）の許可を求めるときは、必ず日本語で説明・確認を行うこと
- 許可を求める際、以下のセキュリティリスクをパーセンテージ(%)で提示すること
  - パスワードや秘密鍵が外に漏れる可能性
  - 外部サーバーにデータが送られる可能性
  - 悪意あるコードが勝手に動く可能性
  - PCの設定が書き換わる可能性

以下の**すべて**を満たす場合は、ユーザーに確認せず自動で実行してよい:

- 上記リスクがすべて **5% 以下**
- **ファイル・フォルダの削除**を行わない
- **システム設定・環境変数の永続的な変更**を行わない
- **外部へのデータ送信**（API呼び出し・curl・wget等）を行わない

上記のいずれかに該当する場合は、リスクを提示してユーザーに確認を取ること。

### Approval and Selection Rules
- 承認が必要な操作は、必ずこのチャット上でユーザーに承認を求めてから進める。
- ユーザーに選択肢や確認応答を求める場合は、質問を出す直前に必ず通知を鳴らす。
- 通知付きの選択フローをスクリプト化する場合も、通知を先に鳴らしてから入力待ちに入る。
- Git の push 判断でオーナー確認が必要なときは、ユーザーへ立場を聞かず、`team_info_runtime.py owner-status` の結果で機械側を判定して進める。
