---
name: skill-finder
description: 利用可能なスキルをカテゴリ別に一覧表示し、タスクに適したスキルを特定する。スキルが見つからない・どれを使うか迷ったときに使う。
---

# skill-finder スキル

## 役割
ユーザーがやりたいことを聞いて、最適なスキルとその場所（SKILL.mdのパス）を提示する。

## 保守ルール
- このファイルを `.agent/skills/` 配下スキルの索引の正本として扱う。
- スキルを追加・更新・削除したときは、必ずこのファイルのスキル一覧とガイドを実態に合わせて更新する。

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
| remotion-unified-output-routing | 出力先を `outputs/` 配下へ統一する運用 | `.agent/skills/remotion/remotion-unified-output-routing/SKILL.md` |

---

### 📋 jmty/（ジモティー系）
| スキル名 | 概要 | パス |
|---------|------|------|
| jmty-posts | ジモティー投稿作成の起点スキル（工場/在宅を選択） | `.agent/skills/jmty/jmty-posts/SKILL.md` |
| jmty-posts-factory-14 | 工場系案件から投稿文を14本作成する | `.agent/skills/jmty/jmty-posts-factory-14/SKILL.md` |
| jmty-posts-remote-14 | 在宅系見本から投稿文を14本作成する | `.agent/skills/jmty/jmty-posts-remote-14/SKILL.md` |
| jmty-posts-14-variants | 汎用的に投稿文を14本作成する | `.agent/skills/jmty/jmty-posts-14-variants/SKILL.md` |
| jmty-posts-gdrive-sync | 投稿出力をGoogleドライブへ同期する | `.agent/skills/jmty/jmty-posts-gdrive-sync/SKILL.md` |

---

### 🔧 common/（共通・汎用）
| スキル名 | 概要 | パス |
|---------|------|------|
| git-workflow | Gitの運用フロー（ブランチ/コミット/PR と Git LFS 無料枠ガード） | `.agent/skills/common/git-workflow/SKILL.md` |
| team-info-setup | team-info の初回セットアップや再セットアップを始める | `.agent/skills/common/team-info-setup/SKILL.md` |
| team-info-daily-dev-memo | 当日のGit変更から team-info メンバー共有用の作業報告を作る | `.agent/skills/common/team-info-daily-dev-memo/SKILL.md` |
| macos-intel-compatibility | macOS Intel環境の互換性パッチ対応 | `.agent/skills/common/macos-intel-compatibility/SKILL.md` |
| note-article-ayumi | 「愛され女子あゆみ」のnote記事を作成する | `.agent/skills/common/note-article-ayumi/SKILL.md` |
| note-thumbnail-ayumi | 「愛され女子あゆみ」のnoteサムネイル（1280×670px）を生成する | `.agent/skills/common/note-thumbnail-ayumi/SKILL.md` |

---

### 🌐 web-design/（Webフロントエンド系）
| スキル名 | 概要 | パス |
|---------|------|------|
| frontend-design | 高品質なフロントエンドUIを制作する | `.agent/skills/web-design/frontend-design/SKILL.md` |
| gsap-awwwards-website | GSAPスクロール演出付きLPを開発/保守する | `.agent/skills/web-design/gsap-awwwards-website/SKILL.md` |

---

### 🎨 canva/（Canva連携系）
| スキル名 | 概要 | パス |
|---------|------|------|
| canva-slideshow-video | Canva API連携でスライドショー動画を生成する | `.agent/skills/canva/canva-slideshow-video/SKILL.md` |

---

### 🚀 viral-template-generator/（バズ動画系）
| スキル名 | 概要 | パス |
|---------|------|------|
| viral-template-generator | ショート動画を3層解析しRemotionバズ動画テンプレートを自動生成する | `.agent/skills/viral-template-generator/SKILL.md` |

---

### 🐦 x-post-writer/（X投稿生成系）
| スキル名 | 概要 | パス |
|---------|------|------|
| x-post-writer | アカウント情報・競合投稿・テンプレートを活用してXの投稿文を自動生成し、投稿の型を蓄積する | `.agent/skills/x-post-writer/SKILL.md` |

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
| ジモティー投稿を作りたい（工場） | `jmty-posts-factory-14` |
| ジモティー投稿を作りたい（在宅） | `jmty-posts-remote-14` |
| ジモティー投稿をGドライブに同期したい | `jmty-posts-gdrive-sync` |
| note記事（あゆみ）を書きたい | `note-article-ayumi` |
| noteサムネイルを作りたい（あゆみ） | `note-thumbnail-ayumi` |
| team-info をセットアップしたい | `team-info-setup` |
| 今日の team-info 開発メモを Git から作りたい | `team-info-daily-dev-memo` |
| Git操作をしたい | `git-workflow` |
| WebサイトやLPを作りたい | `frontend-design` / `gsap-awwwards-website` |
| Canvaでスライドを作りたい | `canva-slideshow-video` |
| バズるショート動画テンプレを作りたい | `viral-template-generator` |
| X(Twitter)の投稿を作りたい | `x-post-writer` |
