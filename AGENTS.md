## Skills
A skill is a set of local instructions stored in a `SKILL.md` file.
From now on, this repository uses only `.agent/skills` as the skills source.

### Available skills
- acoriel-video-description: Acoriel（アコリエル）チャンネルのYouTube動画概要欄を生成する。 (file: /Users/deguchishouma/team-info/.agent/skills/acoriel/acoriel-video-description/SKILL.md)
- remotion-template-acoriel-acoustic-cover: acoriel向けのアコースティックカバー用Remotion編集。 (file: /Users/deguchishouma/team-info/.agent/skills/acoriel/remotion-template-acoriel-acoustic-cover/SKILL.md)
- remotion-video-production: Remotion動画制作の親スキル（チャンネル/テンプレ選択）。 (file: /Users/deguchishouma/team-info/.agent/skills/remotion/remotion-video-production/SKILL.md)
- remotion-template-sleep-travel-long-knowledge-relax: sleep_travel長尺動画テンプレ編集。 (file: /Users/deguchishouma/team-info/.agent/skills/remotion/remotion-template-sleep-travel-long-knowledge-relax/SKILL.md)
- remotion-template-sleep-travel-short-digest: sleep_travel短尺動画テンプレ編集。 (file: /Users/deguchishouma/team-info/.agent/skills/remotion/remotion-template-sleep-travel-short-digest/SKILL.md)
- lyric-video-production: 音声と歌詞からLRC生成とリリック演出を行う。 (file: /Users/deguchishouma/team-info/.agent/skills/remotion/lyric-emotion-mapper/SKILL.md)
- script-writing-accounts-aware: アカウント連動の段階的な台本作成。 (file: /Users/deguchishouma/team-info/.agent/skills/remotion/script-writing-accounts-aware/SKILL.md)
- voice-script-launcher: 台本をVOICEVOXで音声化する実行フロー。 (file: /Users/deguchishouma/team-info/.agent/skills/remotion/voice-script-launcher/SKILL.md)
- remotion-unified-output-routing: 出力先を `outputs/` 配下へ統一する運用。 (file: /Users/deguchishouma/team-info/.agent/skills/remotion/remotion-unified-output-routing/SKILL.md)
- jmty-posts: ジモティー投稿作成の親スキル。 (file: /Users/deguchishouma/team-info/.agent/skills/jmty/jmty-posts/SKILL.md)
- jmty-posts-factory-12: 工場求人向け投稿文を12本作成する。 (file: /Users/deguchishouma/team-info/.agent/skills/jmty/jmty-posts-factory-12/SKILL.md)
- jmty-posts-remote-12: 在宅求人向け投稿文を12本作成する。 (file: /Users/deguchishouma/team-info/.agent/skills/jmty/jmty-posts-remote-12/SKILL.md)
- jmty-posts-12-variants: 案件ファイルから12本の投稿文を作成する。 (file: /Users/deguchishouma/team-info/.agent/skills/jmty/jmty-posts-12-variants/SKILL.md)
- jmty-posts-gdrive-sync: ジモティー投稿出力をGoogleドライブに同期する。 (file: /Users/deguchishouma/team-info/.agent/skills/jmty/jmty-posts-gdrive-sync/SKILL.md)
- git-workflow: Gitの安全なブランチ/コミット/プッシュ手順。 (file: /Users/deguchishouma/team-info/.agent/skills/common/git-workflow/SKILL.md)
- macos-intel-compatibility: Intel MacのPython/PyTorch互換性対応。 (file: /Users/deguchishouma/team-info/.agent/skills/common/macos-intel-compatibility/SKILL.md)
- note-article-ayumi: 「愛され女子あゆみ」のnote記事を作成する。 (file: /Users/deguchishouma/team-info/.agent/skills/common/note-article-ayumi/SKILL.md)
- frontend-design: 高品質なフロントエンドUIを制作する。 (file: /Users/deguchishouma/team-info/.agent/skills/web-design/frontend-design/SKILL.md)
- gsap-awwwards-website: GSAPスクロール演出付きLPを開発/保守する。 (file: /Users/deguchishouma/team-info/.agent/skills/web-design/gsap-awwwards-website/SKILL.md)
- skill-finder: タスクに合うスキルを一覧から特定する。 (file: /Users/deguchishouma/team-info/.agent/skills/skill-finder/SKILL.md)

### How to use skills
- Discovery: Open the relevant `SKILL.md` and read only what is needed for the current task.
- Trigger rules: If the user names a skill (with `$SkillName` or plain text), use that skill in the same turn.
- Path resolution: Resolve relative paths from each skill directory first.
- Reuse first: Prefer scripts/templates/assets inside the skill over recreating artifacts.
- Coordination: If multiple skills apply, use the minimal set and state the order briefly.
- Fallback: If a skill is missing or unclear, state the issue briefly and continue with the best practical approach.
