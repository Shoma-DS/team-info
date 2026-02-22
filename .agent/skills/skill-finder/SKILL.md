---
name: skill-finder
description: 利用可能なスキルをカテゴリ別に一覧表示し、タスクに適したスキルを特定する。スキルが見つからない・どれを使うか迷ったときに使う。
---

# skill-finder スキル

## 役割
ユーザーがやりたいことを聞いて、最適なスキルとその場所（SKILL.mdのパス）を提示する。

## 使い方
1. ユーザーのやりたいことを確認する（例: 「ジモティー投稿を作りたい」「アコリエルの動画を作りたい」）
2. 下記のカテゴリ一覧からマッチするスキルを探す
3. 該当スキルの SKILL.md を読み込み、そのスキルとして動作する

---

## スキル一覧

### 🎸 acoriel/（アコリエル系）
| スキル名 | 概要 | パス |
|---------|------|------|
| remotion-template-acoriel-acoustic-cover | アコリエルのリリックビデオをRemotionで制作する | `.agent/skills/acoriel/remotion-template-acoriel-acoustic-cover/SKILL.md` |
| acoriel-video-description | アコリエルのYouTube概要欄を生成する | `.agent/skills/acoriel/acoriel-video-description/SKILL.md` |

---

### 📹 remotion/（Remotion・動画制作系）
| スキル名 | 概要 | パス |
|---------|------|------|
| remotion-video-production | Remotionチャンネル・テンプレ選択の起点スキル | `.agent/skills/remotion/remotion-video-production/SKILL.md` |
| remotion-template-sleep-travel-long-knowledge-relax | 寝ながらトラベル・長尺知識リラックス動画 | `.agent/skills/remotion/remotion-template-sleep-travel-long-knowledge-relax/SKILL.md` |
| remotion-template-sleep-travel-short-digest | 寝ながらトラベル・短尺ダイジェスト動画 | `.agent/skills/remotion/remotion-template-sleep-travel-short-digest/SKILL.md` |
| lyric-video-production | 音声・歌詞からLRC生成→Remotionリリックアニメーション制作 | `.agent/skills/remotion/lyric-emotion-mapper/SKILL.md` |
| voice-script-launcher | 台本ファイルから音声を一括生成する | `.agent/skills/remotion/voice-script-launcher/SKILL.md` |
| script-writing-accounts-aware | アカウントごとのトーンで台本を作成する | `.agent/skills/remotion/script-writing-accounts-aware/SKILL.md` |

---

### 📋 jmty/（ジモティー系）
| スキル名 | 概要 | パス |
|---------|------|------|
| jmty-posts | ジモティー投稿作成の起点スキル（工場/在宅を選択） | `.agent/skills/jmty/jmty-posts/SKILL.md` |
| jmty-posts-factory-12 | 工場系案件から投稿文を12本作成する | `.agent/skills/jmty/jmty-posts-factory-12/SKILL.md` |
| jmty-posts-remote-12 | 在宅系見本から投稿文を12本作成する | `.agent/skills/jmty/jmty-posts-remote-12/SKILL.md` |
| jmty-posts-12-variants | 汎用的に投稿文を12本作成する | `.agent/skills/jmty/jmty-posts-12-variants/SKILL.md` |
| jmty-posts-gdrive-sync | 投稿出力をGoogleドライブへ同期する | `.agent/skills/jmty/jmty-posts-gdrive-sync/SKILL.md` |

---

### 🔧 common/（共通・汎用）
| スキル名 | 概要 | パス |
|---------|------|------|
| git-workflow | Gitの運用フロー（ブランチ/コミット/PR） | `.agent/skills/common/git-workflow/SKILL.md` |
| macos-intel-compatibility | macOS Intel環境の互換性パッチ対応 | `.agent/skills/common/macos-intel-compatibility/SKILL.md` |
| note-article-ayumi | 「愛され女子あゆみ」のnote記事を作成する | `.agent/skills/common/note-article-ayumi/SKILL.md` |

---

## ガイド：やりたいこと別

| やりたいこと | 使うスキル |
|------------|----------|
| アコリエルの動画を作りたい | `remotion-template-acoriel-acoustic-cover` |
| アコリエルの概要欄を作りたい | `acoriel-video-description` |
| 寝ながらトラベルの動画を作りたい | `remotion-video-production`（起点）→ テンプレ選択 |
| 歌詞字幕・カラオケ動画を作りたい | `lyric-video-production` |
| 台本から音声を生成したい | `voice-script-launcher` |
| YouTube台本を書きたい | `script-writing-accounts-aware` |
| ジモティー投稿を作りたい（工場） | `jmty-posts-factory-12` |
| ジモティー投稿を作りたい（在宅） | `jmty-posts-remote-12` |
| ジモティー投稿をGドライブに同期したい | `jmty-posts-gdrive-sync` |
| note記事（あゆみ）を書きたい | `note-article-ayumi` |
| Git操作をしたい | `git-workflow` |
