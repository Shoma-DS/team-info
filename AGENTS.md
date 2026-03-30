## 開発モード管理（全エージェント共通・必須）

**このルールは Claude・Codex・Gemini など、すべての AI エージェントに適用される。**

### モードの確認（作業開始前に必須）

新規ファイル・フォルダの作成を伴うタスクを開始する前に、**必ず** `.dev-mode` ファイルを読み込み、現在のモードをユーザーに提示して確認すること。

```
現在のモード: チーム開発モード  ← または 個人開発モード
このまま続けてよいですか？
```

### チーム開発モード（`.dev-mode` の内容が `team`）

- 新規ファイル・フォルダは通常どおり git の追跡対象
- `.gitignore` への自動追加は行わない

### 個人開発モード（`.dev-mode` の内容が `personal`）

- 新規作成したファイル・フォルダのパスを、**作成直後に** `.gitignore` へ追記すること
- 追記形式: `# [personal] {作成日YYYY-MM-DD}` コメントとともにパスを追加
- 既存ファイルへの変更はこのルールの対象外

### モード切り替えコマンド

| コマンド | 動作 |
|---------|------|
| `/team` | チーム開発モードに切り替え（`.dev-mode` に `team` を書き込む） |
| `/personal` | 個人開発モードに切り替え（`.dev-mode` に `personal` を書き込む） |

切り替え後は現在のモードをユーザーに報告すること。

---

## Slash Commands

ユーザーが `/コマンド名` を入力したときは、対応するスキルを即座に読み込んで動作すること。

| コマンド | 読み込むスキル |
|---------|--------------|
| `/acoriel` | `.agent/skills/acoriel/remotion-template-acoriel-acoustic-cover/SKILL.md` |
| `/c` | コミットのみ（push・PR なし）。オーナー機→main、それ以外→アカウント名ブランチ |
| `/git` | `.agent/skills/common/git-workflow/SKILL.md` → コミット＋プッシュ（オーナー機以外は PR 作成） |
| `/pull` | origin/main から最新を取り込む（`git fetch` → `pull --rebase`） |
| `/setup` | `.agent/skills/common/team-info-setup/SKILL.md` |
| `/reach` | `.agent/skills/common/agent-reach/SKILL.md` |
| `/sleep-travel` | `.agent/skills/remotion/remotion-video-production/SKILL.md` |
| `/lyric` | `.agent/skills/remotion/lyric-emotion-mapper/SKILL.md` |
| `/voice` | `.agent/skills/remotion/voice-script-launcher/SKILL.md` |
| `/jmty` | `.agent/skills/jmty/jmty-posts/SKILL.md` |
| `/script` | `.agent/skills/remotion/script-writing-accounts-aware/SKILL.md` |
| `/gdrive` | `.agent/skills/common/gdrive-copy/SKILL.md` |
| `/tyoudoii-illust-fetcher` | `.agent/skills/web-design/tyoudoii-illust-fetcher/SKILL.md` |
| `/themeisle-illustration-fetcher` | `.agent/skills/web-design/themeisle-illustration-fetcher/SKILL.md` |

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
- 30秒以上かかる可能性が高いコマンド、待ち時間が長い解析・レンダリング・重いテスト・常駐プロセス起動は、原則としてエージェントが勝手に実行せず、ユーザー実行に切り替える。
- 長時間コマンドをユーザーに依頼する場合は、目的を短く添えたうえで、コピーしやすい絶対パスのコマンドをそのまま渡し、実行完了の報告を待ってから次に進む。
- Docker / VOICEVOX などの常駐系は、原則として必要なときだけ起動し、不要になったら停止してPC負荷を戻す運用を優先する。
- Docker Compose プロジェクトは、短時間の中断なら `stop`、その作業で不要になったら `down` を優先し、常時起動のまま放置しない。
- 明確な範囲を超える変更や影響の大きい変更は、必ずユーザー確認を取る。
- ユーザーとの対話は原則日本語で行う。
- ユーザーが明示しない限り `.gitignore` は変更しない。必要なら事前に許可を取る。
- Git関連操作を行う場合は、必ず `.agent/skills/common/git-workflow/SKILL.md` を使う。

## Command Path Rules
- ユーザーにコマンドを渡すときは、**必ず絶対パス**で書く。
- ただし新しいパソコンで最初に案内する `setup/setup_all.cmd` だけは、ユーザーがリポジトリルートにいる前提で `./setup/setup_all.cmd` / `.\setup\setup_all.cmd` の相対パス案内を許可する。
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
  - Docker 停止/状態確認: `bash "$TEAM_INFO_ROOT/run.sh" --project [n8n|dify] --action [stop|down|start|restart|ps] ...`
  - Windows の Docker 起動: `& "$env:TEAM_INFO_ROOT\\run.ps1" -Project [n8n|dify] ...`
  - Windows の Docker 停止/状態確認: `& "$env:TEAM_INFO_ROOT\\run.ps1" -Project [n8n|dify] -Action [Stop|Down|Start|Restart|Ps] ...`
- ユーザー指定の入力/出力パスが入る場合も、`"$TEAM_INFO_ROOT/..."` や `"[出力先の絶対パス]"` のように絶対パス前提で案内する。

## Docker Lifecycle Rule
- `dify` や `n8n` などの compose プロジェクトは、必要時に `up` / `start` し、使い終わったら `stop` または `down` する。
- 単発の解析・検証用 Docker コンテナは、処理完了後または不要と判断した時点で停止する。
- `VOICEVOX` は必要時のみ起動し、使い終わったら `team_info_runtime.py stop-voicevox-engine` で停止する。
- `image` や `volume` は再利用前提で保持してよく、通常運用では `docker image prune` や `docker system prune` を前提にしない。

## New Machine Rule
- 作業開始時は、まず `team_info_runtime.py worked-before-status` 相当で、そのパソコンが過去に `team-info` で作業したことがあるかを確認する。
- 判定にはローカル設定ディレクトリの `worked_before_machines.json` を使う。
- 結果が `known` なら、通常どおり作業を進めてよい。
- 結果が `new` なら、最初に `マニュアル/まずはこちらをお読みください.md` を読み込み、その流れに沿ってセットアップを始める。
- `setup-local-machine` や `setup/setup_all.cmd` が終わったら、このパソコンは自動で `worked_before_machines.json` に記録される前提で扱う。
- 新しいパソコンでのセットアップが終わったら、ユーザーへもう一度 `マニュアル/まずはこちらをお読みください.md` を読むように促す。
- それでもユーザーがわからない場合は、止まった画面のスクリーンショットを添えて次の Discord へ質問するよう案内する。
- Discord 案内先: `https://discord.com/channels/1478351976168165511/1479287635535990794`

### Skill Discovery Policy

- `AGENTS.md` には個別スキル一覧を詳細に持たない。最新のスキル索引は `.agent/skills/skill-finder/SKILL.md` とする。
- `/コマンド` は上の固定マッピングに従って対応する。
- `/コマンド` 以外で、ユーザーがスキル利用を明示した場合は、まず `skill-finder` を使って該当スキルを特定する。
- ユーザーがスキル利用を明示していない場合は、先に「スキルを使うか」を確認する。
- ユーザーがスキルを使わないと答えた場合は、`skill-finder` を開かず、スキル探索もせずに通常対応する。
- ユーザーがスキルを使うと答えた場合のみ、`skill-finder` を使って該当スキルを探す。

### Skill maintenance rules
- `.agent/skills/skill-finder/SKILL.md` を、このリポジトリのスキル索引の正本として扱う。
- 新しいスキルを `.agent/skills/` に追加したときは、**必ず** `.agent/skills/skill-finder/SKILL.md` のスキル一覧とガイドを更新すること。
- 既存スキルの概要・パス・用途が変わったとき、またはスキルを削除したときも同様に更新すること。
- スキル作成・更新タスクでは、完了前に `skill-finder` の内容が `.agent/skills/**/SKILL.md` の実態と一致しているか確認すること。

### How to use skills
- Discovery: スキルを使うと決まったときだけ `skill-finder` を開き、該当スキルを特定する。
- Loading: 特定後は対象の `SKILL.md` を開き、現在のタスクに必要な範囲だけ読む。
- Path resolution: 相対パスは各スキルディレクトリ基準で解決する。
- Reuse first: スキル内の scripts/templates/assets を優先して再利用する。
- Coordination: 複数スキルが必要な場合は最小構成に絞り、使う順番を短く示す。
- 画像ダウンロード / イラスト取得系スキルが2つ以上候補に上がる場合は、自動で決めず、候補の違いを短く示してからどれを使うか必ずユーザーに確認する。
- Fallback: スキルが見つからない、または不明瞭な場合は、その旨を短く伝えて実用的な代替手段で進める。

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
