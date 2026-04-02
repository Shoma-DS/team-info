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

## 新規スキル作成ルール（必須）

新しいスキルを作成するときは、以下のルールを必ず守る。

### Google Drive コピールール
- **ファイル・動画・テキストなど「生成物」が出るスキルは、必ずGoogle Driveへのアップロード手順を含める。**
- コピー先は `team-info/outputs/` 以下に、チャンネルや用途に合ったサブフォルダを設ける。
- コピーコマンドは「ユーザーに提示するだけ・Claude自身は実行しない」形式にする。
- Google Drive for Desktop のローカルパスには依存しない。rclone + フォルダID で統一する。

**コピーコマンドのテンプレート（SKILL.md に記載する形式）：**
```bash
rclone copy "$TEAM_INFO_ROOT/[出力ファイルパス]" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/[フォルダ名]/" --progress
```
- rclone が未設定の場合は `.agent/skills/common/gdrive-copy/SKILL.md` の初回セットアップ手順を案内する文言をセットで記載する。

**既存の Google Drive フォルダ（outputs/ 直下）：**
| フォルダ名 | 用途 |
|-----------|------|
| `アコリエル/` | acoriel チャンネルのレンダリング動画 |
| `アコリエル/概要欄/` | acoriel チャンネルの YouTube 概要欄 MD |
| `jmty_posts/` | ジモティー投稿テキスト |
| `寝ながらトラベル/` | sleep_travel チャンネルのレンダリング動画 |
| `note記事/` | 愛され女子あゆみ の note 記事 MD |

新規チャンネル・新規用途の場合は上記に追加し、このテーブルも更新すること。

## 使い方
1. ユーザーのやりたいことを確認する（例: 「ジモティー投稿を作りたい」「アコリエルの動画を作りたい」）
2. 下記のカテゴリ一覧からマッチするスキルを探す
3. 該当スキルの SKILL.md を読み込み、そのスキルとして動作する

## 画像ダウンロード系の選択ルール
- 画像ダウンロード / イラスト取得系スキルが2つ以上候補に上がる場合は、自動選択しない。
- 候補の違いを短く説明したうえで、どれを使うか必ずユーザーに確認する。
現在の代表例:
- `themeisle-illustration-fetcher`: 汎用のWebサイト向け、SaaS / LP 向け、SVG を活かしやすい海外テイスト
- `tyoudoii-illust-fetcher`: 日本語サイト向け、親しみやすい国内イラスト

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
| team-info-setup | team-info の初回セットアップや再セットアップを始める。core setup と lazy bootstrap 方針の入口 | `.agent/skills/common/team-info-setup/SKILL.md` |
| agent-reach | team-info 向けに取り込んだ Agent-Reach。初回は自動 bootstrap しつつ、OpenClaw / Codex から Web・SNS・動画・RSS・GitHub を横断調査する | `.agent/skills/common/agent-reach/SKILL.md` |
| repo-adapted-tool-import | 外部リポジトリ、CLI、AI skill、MCP サーバーなどを team-info の運用に合わせて取り込む。現在の repo を優先して衝突を吸収する | `.agent/skills/common/repo-adapted-tool-import/SKILL.md` |
| obsidian-claudian | official Obsidian CLI と Claudian を team-info 向けに導入・更新し、active vault の plugin、`.claude/` 初期設定、初期 subagent 雛形を整える | `.agent/skills/common/obsidian-claudian/SKILL.md` |
| shared-agent-assets | 複数 repo で共有するルール・スキル資産を team-info 流儀で同期する。`AGENTS.md` と `.agent/skills` を正本のまま維持する | `.agent/skills/common/shared-agent-assets/SKILL.md` |
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
| clone-website | browser automation を使ってサイトを pixel-perfect に再構築する。global setup へ依存を載せず、bundled Next.js 16 テンプレを初期化して複製作業に入る | `.agent/skills/web-design/clone-website/SKILL.md` |
| tyoudoii-illust-fetcher | tyoudoii-illust.com の無料イラストを REST API 経由で検索・取得し、Webプロジェクトへ組み込む | `.agent/skills/web-design/tyoudoii-illust-fetcher/SKILL.md` |
| themeisle-illustration-fetcher | Themeisle Illustrations の PNG / SVG を選び、Webプロジェクトへ組み込む | `.agent/skills/web-design/themeisle-illustration-fetcher/SKILL.md` |

---

### 🎨 canva/（Canva連携系）
| スキル名 | 概要 | パス |
|---------|------|------|
| canva-slideshow-video | 台本から構造化 manifest を作り、Remotion で見せ方を出し分けるスライドショー動画を生成する | `.agent/skills/canva/canva-slideshow-video/SKILL.md` |
| canva-slide-design-extender | Canva のテンプレや既存デザインを崩さずに、新しいスライドを追加・増築する | `.agent/skills/canva/canva-slide-design-extender/SKILL.md` |

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
| X / Reddit / YouTube / GitHub / 小紅書などを横断調査したい | `agent-reach` |
| OpenClaw に team-info 版 Agent-Reach を入れたい | `agent-reach` |
| 外部ツールや外部 repo を team-info 向けに取り込みたい | `repo-adapted-tool-import` |
| 何かを導入するとき、今の repo 優先で書き換えて入れたい | `repo-adapted-tool-import` |
| official Obsidian CLI と Claudian を入れたい | `obsidian-claudian` |
| Obsidian の active vault に Claudian を入れたい | `obsidian-claudian` |
| 複数 repo で共有ルール・共有スキルを一元管理したい | `shared-agent-assets` |
| SessionStart Hook で shared repo を自動更新したい | `shared-agent-assets` |
| 今日の team-info 開発メモを Git から作りたい | `team-info-daily-dev-memo` |
| Git操作をしたい | `git-workflow` |
| WebサイトやLPを作りたい | `frontend-design` / `gsap-awwwards-website` |
| 既存サイトをそっくり Next.js で作り直したい | `clone-website` |
| サイトを pixel-perfect に複製したい | `clone-website` |
| LPの絵文字や仮アイコンを、ちょうどいいイラストの画像に差し替えたい | `themeisle-illustration-fetcher` |
| Themeisle のイラストをダウンロードしてサイトに使いたい | `themeisle-illustration-fetcher` |
| 日本語テイストのやわらかいイラストに差し替えたい | `tyoudoii-illust-fetcher` |
| CanvaやRemotionで台本からスライドショー動画を作りたい | `canva-slideshow-video` |
| Canvaのテンプレや既存資料を維持して、新しいページを足したい | `canva-slide-design-extender` |
| バズるショート動画テンプレを作りたい | `viral-template-generator` |
| X(Twitter)の投稿を作りたい | `x-post-writer` |
