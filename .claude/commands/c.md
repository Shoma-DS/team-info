これは Claude Code 用の互換ラッパーです。正本は `AGENTS.md` の `/c` ルールです。

変更内容をコミットします。プッシュ・プルリクエストは行いません。

## 手順

### 1. 変更確認

`git -C "$TEAM_INFO_ROOT" status` と `git -C "$TEAM_INFO_ROOT" diff --staged` で変更内容を把握する。
ステージされていない変更は `git -C "$TEAM_INFO_ROOT" add -A` でステージする。

### 2. オーナー機かを確認する

`python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" owner-status` を実行する。

**オーナー機（結果が `owner`）の場合:**
- 現在のブランチが `main` でなければ `git -C "$TEAM_INFO_ROOT" checkout main` で切り替える
- そのまま main ブランチでコミットする

**オーナー機以外（結果が `other`）の場合:**
- `git -C "$TEAM_INFO_ROOT" config user.name` でアカウント名を取得する
- アカウント名をケバブケースに変換してブランチ名にする（例: `Shoma Deguchi` → `shoma-deguchi`）
- そのブランチが存在しなければ `git -C "$TEAM_INFO_ROOT" checkout -b <アカウント名ブランチ>` で作成する
- 既に存在すれば `git -C "$TEAM_INFO_ROOT" checkout <アカウント名ブランチ>` で切り替える
- そのブランチでコミットする

### 3. コミット内容をユーザーに説明して承認を得る

変更内容を以下の形式で説明する:

```
<1行での要約>

全体像:
<この変更が何のためか>

変更したファイル:
- <ファイル名>: <どのように変えたか>
```

コミットメッセージ案（要約＋詳細3〜5行）を提示し、「この内容でコミットして良いですか？」と確認する。
承認が得られた場合のみコミットを実行する。

### 4. コミット実行

```bash
git -C "$TEAM_INFO_ROOT" commit -m "<1行要約>

<詳細>"
```

コミット完了後、以下を報告する:
- コミットしたブランチ名
- コミットハッシュ（短縮形）
- プッシュは行っていない旨

## 注意
- push は絶対に行わない
- プルリクエストも作成しない
- コミットメッセージは `.agent/skills/common/git-workflow/SKILL.md` のルールに従う（小学生にもわかる言葉で）
