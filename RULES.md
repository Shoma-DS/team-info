# RULES.md — team-info リポジトリ運用ルール

> AI・人間どちらも参照するルール定義ファイル。
> このリポジトリに変更を加える場合は、必ずこのファイルのルールに従うこと。

---

## 1. フォルダ命名規則

| 種別 | 規則 | 例 |
|---|---|---|
| トップレベルフォルダ | PascalCase または kebab-case（英語） | `Remotion/`, `projects/` |
| スキルフォルダ | kebab-case（英語） | `acoriel-video-description/` |
| 入力フォルダ | kebab-case（英語） | `inputs/viral-analysis/` |
| 出力フォルダ | kebab-case（英語） | `outputs/acoriel/descriptions/` |
| 個人アカウントフォルダ | lowercase 英数字 | `personal/deguchishouma/` |
| Remotion Composition ID | `{Channel}-{Name}-{Variant}` | `AcoRiel-Diamond-Princess-MultiBG` |
| 出力ファイル（動画・音声） | スネークケース or ハイフン区切り | `output.mp4`, `bg_prerendered.mp4` |

**原則: 新しいフォルダは英語 + kebab-case で作成する。**
既存の日本語フォルダ名（`YouTube競合リサーチ/`, `マニュアル/`）はリネーム時に英語化する。

---

## 2. フォルダ用途マップ

```
team-info/
├── .agent/skills/         AIスキル定義（SKILL.md + スクリプト）
├── inputs/                解析・生成の素材インボックス
│   ├── jmty_cases/        ジモティー案件素材
│   ├── jmty_factory_cases/ 工場求人素材
│   ├── jmty_remote_samples/ 在宅求人素材
│   └── viral-analysis/    バズ動画解析インボックス（.mp4 を置く）
├── outputs/               共有で扱う生成物の出力先
│   ├── acoriel/
│   │   ├── descriptions/ アコリエル YouTube 概要欄 .md
│   │   └── renders/      アコリエル動画レンダリング出力
│   ├── common/            汎用出力
│   ├── jmty/              ジモティー投稿文
│   ├── note/              note 記事
│   ├── sleep_travel/      寝ながらトラベル動画出力
│   └── viral-analysis/    バズ動画解析結果（analysis.json + remotion/）
├── personal/              個人用ファイルの集約先
│   └── <account>/         Git アカウント名を元にした個人フォルダ
│       ├── discord/       Webhook や個人通知設定
│       ├── gas/           個人用 Google Apps Script
│       ├── kpi/           月次 KPI や週次計画
│       ├── outputs/       個人用の生成物・レポート・下書き成果物
│       ├── projects/      個人案件・個人ツール・ OpenEmpire など
│       └── scripts/       個人専用の補助スクリプトや定期実行物
├── Remotion/              Remotion 動画制作環境
│   ├── my-video/          メイン Remotion プロジェクト（npm run）
│   ├── scripts/           Remotion 補助スクリプト（Python）
│   └── script_resources/  台本・歌詞サンプル
├── projects/              継続開発する共有・検証用のソース置き場
│   └── test-website/      独立した Web サイト開発用プロジェクト
├── scripts/               共有の補助スクリプト
├── GAS/                   共有の Google Apps Script
├── docker/                Docker 構成（Dify 等）
├── mcp-servers/           MCP サーバー定義
└── マニュアル/            人向けマニュアル
```

---

## 3. AI コンテキストファイルルール

- **AGENTS.md**（ルート）: Claude Code / AI エージェント向けの総合指示書。行動原則・承認方針・Slash Commands・Git運用の正本。
- **CLAUDE.md**（ルート）: Claude Code 向けの薄い入口ファイル。正本ではなく、`AGENTS.md` と `RULES.md` への案内に徹する。
- **CLAUDE.md**（サブフォルダ）: そのフォルダを開いたときに AI が即座に文脈を把握するためのファイル。
  - 配置基準: AI が作業するフォルダすべてに置く
  - 内容: フォルダ用途・配下構造・注意事項・よく使うコマンド
- **RULES.md**（ルート）: このファイル。命名規則・禁止事項・フォルダ構造の正本。

---

## 4. スキル（.agent/skills/）ルール

- スキルフォルダは必ず `SKILL.md` を含む
- スキル追加後は必ず `.agent/skills/skill-finder/SKILL.md` の索引を更新する
- スキルの入力素材は `inputs/{skill-name}/` へ置く
- 共有スキルの出力は `outputs/{skill-name}/`、個人スキルの出力は `personal/<account>/outputs/{skill-name}/` を原則にする
- 個人専用スキルは `.agent/skills/personal/<account>/` 配下へ置き、共有スキルと混ぜない
- `AGENTS.md` には個別スキル一覧を増やさず、索引の正本は `.agent/skills/skill-finder/SKILL.md` に寄せる

**スキルカテゴリ:**
| カテゴリ | フォルダ | 用途 |
|---|---|---|
| acoriel | `.agent/skills/acoriel/` | アコリエルチャンネル動画制作 |
| remotion | `.agent/skills/remotion/` | Remotion 動画全般 |
| jmty | `.agent/skills/jmty/` | ジモティー投稿文生成 |
| common | `.agent/skills/common/` | 汎用（Git・OS互換・note記事等） |
| web-design | `.agent/skills/web-design/` | Web フロントエンド制作 |
| viral-template-generator | `.agent/skills/viral-template-generator/` | バズ動画テンプレ自動生成 |

---

## 5. 禁止事項

### 絶対禁止
- `AGENTS.md` を削除・移動すること（AI の行動指針が失われる）
- APIキー・シークレット・`.env` を Git にコミットすること
- `Remotion/my-video/node_modules/` を Git に追加すること
- `outputs/` 配下の生成ファイルを `inputs/` に置くこと（逆方向の混入）

### 原則禁止
- 新規フォルダを日本語名で作成すること（既存は許容）
- スキルフォルダに `SKILL.md` を含めずに作成すること
- `inputs/` 配下に出力ファイルを置くこと
- root 直下に単発の `.html` / `.pdf` / 画像 / プレビュー資料を置くこと

### root 直下に置いてよいもの
- `AGENTS.md`、`Agent.md`、`CLAUDE.md`、`RULES.md`、`README.md` のような repo の正本・入口
- `run.sh`、`run.ps1` のような repo 共通ランチャー
- dotfile / 設定ファイル（例: `.gitignore`, `.mcp.json`, `.gemini/`, `.claude/`）
- それ以外の案件資料・プレビュー・納品物は、対応する案件フォルダまたは `outputs/` 配下へ移動する

### 互換・旧構成の扱い
- `Remotion/my-video/` を Remotion 正本として扱い、新しい作業先や案内先は必ずこちらへ寄せる
- root 直下の `my-video/` は旧構成との互換用の空き導線として扱い、新規ファイルや新規運用を置かない
- note 記事の出力先は `outputs/note/` に統一する
- 共有 Apps Script は `GAS/`、個人用 Apps Script は `personal/<account>/gas/` に分ける
- 個人用スクリプトは `scripts/personal/<account>/` を増やさず、`personal/<account>/scripts/` に集約する
- 個人用の成果物は `outputs/personal/` を増やさず、`personal/<account>/outputs/` へ寄せる
- `test-website/` のような独立プロジェクトは root 直下に増やさず、`projects/` 配下へ寄せる

---

## 6. Git 運用ルール

- ブランチ・コミット・プッシュは必ず `.agent/skills/common/git-workflow/SKILL.md` のフローに従う
- `git push` はオーナー確認後に実行（`team_info_runtime.py owner-status` で判定）
- バイナリファイル（`.mp4`, `.mp3`, 大容量 `.png`）は原則 Git 管理外（`.gitignore` 確認）
