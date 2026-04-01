---
name: git-workflow
description: 変更内容をリモートリポジトリに反映するためのGit操作セット。ブランチ作成、コミット、プッシュの一連の流れを安全に実行します。プッシュ先は原則として `origin` (team-info) です。
---

# Git ワークフロースキル

## 絶対パスルール（必須）
- ユーザーに Git コマンドを見せるときは、固定の `/Users/...` ではなく `TEAM_INFO_ROOT` を使って絶対パスを組み立てる。
- `git status` のように短く書かず、`git -C "$TEAM_INFO_ROOT" status` の形で渡す。
- 新しいパソコンでは、リポジトリルートで `python .agent/skills/common/scripts/team_info_runtime.py setup-local-machine --repo-root .` を 1 回実行して `TEAM_INFO_ROOT` を決める。
- オーナー機として使うパソコンだけ、上のコマンドに `--owner` を付ける。
- `cd` を使う場合も、移動先は `"$TEAM_INFO_ROOT/..."` の形にする。

## 事前確認 (Pre-flight Check)
スキル実行前に必ず `git -C "$TEAM_INFO_ROOT" status` を確認し、未コミットの変更があるか把握すること。

## Git LFS 無料枠ルール（必須）
- Git LFS を使う push は、GitHub Free の無料枠を超えそうなら**必ず拒否**する。
- push の前に、次を実行して結果を確認する。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" git-lfs-free-plan-status --remote-name origin
```

- 上のコマンドが非 0 で終わったら、push してはいけない。
- 拒否時は、ユーザーへ次の 3 点を必ず伝える。
  1. 何が原因で止まったか
  2. いまの見込み容量がどれくらいか
  3. どう直せば無料枠のまま進められるか
- `setup-local-machine` 後は `.githooks/pre-push` が自動で有効になる前提で扱う。手元で `git push` しても同じ判定で止まる。
- 同じ GitHub アカウントで他のリポジトリでも LFS を使うときは、予約分を差し引いて判定する。

```bash
git -C "$TEAM_INFO_ROOT" config team-info.lfsReservedBytes <バイト数>
```

- 予約分を一時的に環境変数で渡すなら、macOS / Linux は `TEAM_INFO_GIT_LFS_RESERVED_BYTES`、Windows は `$env:TEAM_INFO_GIT_LFS_RESERVED_BYTES` を使う。

## Discord 自動報告（任意）
- `/git` の push / プルリクエスト完了後に Discord へ自動報告したい場合は、ユーザーが明示的に希望しているときだけ使う。
- チームで同じ Webhook を使うときは、`config/discord-git-webhook.json` を Git 共有の正本にしてよい。
- 読み取り順は `--webhook-url` → 環境変数 → `config/discord-git-webhook.json` → ローカル設定 の順にする。

- チーム共有の設定:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-set --url "<Discord Webhook URL>"
```

- 共有設定ファイルの場所:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-path
```

- 個人だけで一時的に上書きしたいとき:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-set --url "<Discord Webhook URL>"
```

- 設定確認:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-status
```

- 解除:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-clear
```

- 共有設定の解除:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-webhook-shared-clear
```

- Discord に送る本文は、コミットメッセージと変更ファイル名から、小学生にもわかる短い文へまとめる。
- push / PR の前に、報告対象の基点として `origin/main` の SHA を控えておく。
- push / PR が成功したあとに、次のどちらかを実行する。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-report --event push --base-sha "<push前に控えた origin/main の SHA>" --head-sha HEAD
```

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" discord-git-report --event pr --base-sha "<push前に控えた origin/main の SHA>" --head-sha HEAD --pr-title "<PR タイトル>" --pr-url "<PR URL>"
```

- Webhook が未設定なら、Git の処理は成功として進めつつ、「Discord 送信だけスキップした」とユーザーへ伝える。
- Discord 送信だけ失敗した場合も、push / PR 成功と通知失敗を分けて報告する。

## コミットメッセージのルール (厳守)

コミットメッセージは以下のフォーマットで作成すること。

```text
<1行要約: 小学生でもわかる短い言葉で書く>

<詳細: 小学生でもわかる言葉で、何をしたかを細かく書く>
```

### 詳細メッセージの書き方（必須）
- むずかしい専門用語をできるだけ使わない。
- 1文を短くする（目安: 40文字以内）。
- 「どこを変えたか」「何をしたか」「何がよくなるか」をはっきり書く。
- 詳細は**3〜5行**で書く。短すぎる説明で終わらせない。
- 変更したファイル名やフォルダ名を、できるだけそのまま書く。
- `AGENTS.md` や `src/app.ts` のように、実際の名前を出す。
- 「案内の紙」「道具」「場所」などのぼかした言い方だけで済ませない。
- 新しいファイルを足したときは、「`CLAUDE.md` を作った」のように書く。
- できるだけ次の順番で書く。
  1. どこをさわったか
  2. 何を足したか、または直したか
  3. それで何が楽になるか
  4. 必要なら気をつける点
- カタカナ語や省略語をそのまま使わない。
- NG例: 「リファクタリング」「依存解決」「最適化」「クロスプラットフォーム対応」
- 言いかえ例:
  - `リファクタリング` → `書き方を整理した`
  - `依存解決` → `足りない道具を入れた`
  - `最適化` → `むだな動きを減らした`
  - `クロスプラットフォーム対応` → `いろいろなパソコンで動きやすくした`

### 詳細メッセージの型（推奨）

```text
<1行要約>

<どこをさわったか>
<何をしたか>
<何がよくなるか>
<必要なら補足>
```

### 自分での見直し（必須）
- コミット前に、詳細文を読み返して「小学5年生が読んでわかるか」を確認する。
- わかりにくい言葉があれば、もっとやさしい言い方に直す。
- 1行で意味が2つ以上入っていたら、2行に分ける。
- 「設定」「対応」「改善」だけで終わる文を作らない。
- 抽象的な言いかえだけになっていないか確認する。
- 読み返して、変更したファイル名が1つも出ていなければ書き直す。

**例（推奨）:**
```text
機能Aのバグ修正

`src/input.ts` の見方を直しました。
空っぽのままだと止まる所を直しました。
先に中身を見る順に変えました。
前よりエラーが出にくくなります。
```

**例（もっと細かい形）:**
```text
動画を入れる場所を足した

`inputs/videos/` を足しました。
`.gitkeep` を入れて空でも残るようにしました。
`package.json` に使う命令を足しました。
次の作業をすぐ始めやすくなります。
```

## 必須フロー (ワークフロー)

### 0. 状態の把握（最初に必ず実行）

```bash
git -C "$TEAM_INFO_ROOT" status
git -C "$TEAM_INFO_ROOT" log origin/main..HEAD --oneline
```

上記の結果から、次の 2 つを確認する。

| 確認項目 | 判定 |
|---------|------|
| 未コミットの変更がある | → ステップ 1〜3（コミット→プッシュ）へ |
| 未コミットはないが、未プッシュのコミットがある | → ステップ 3（プッシュのみ）へ |
| 何も変更なし | → 「変更はありません」とユーザーに伝えて終了 |

### 1. 変更のステージング (`git add`)
- 未コミットの変更がある場合のみ実行する。
- ユーザーへの確認は**不要**。
- `git -C "$TEAM_INFO_ROOT" add -A` でステージングする。

### 2. オーナー機かを確認する
- `python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" owner-status` を実行する。
- 結果が `owner` なら、このパソコンをオーナー機として扱う。
- 結果が `other` なら、オーナー機ではないとして扱う。
- ユーザーに「あなたは誰ですか？」とは聞かない。
- オーナー判定が取れない場合も、安全側で `other` として扱う。

**ブランチ準備（オーナー・非オーナー共通）:**
- 事前にアカウント名ブランチを作成・移動する必要はありません。
- 原則として、全員まずは `main` ブランチ上にとどまり、そこで変更のステージングとコミットを行ってください。

### 3. コミット前の説明と承認 (`git commit`)
- 未コミットの変更がない場合はこのステップをスキップする。
- **コミットを実行する前に**、以下の手順を踏むこと。
  1. `git -C "$TEAM_INFO_ROOT" diff --staged` 等で変更内容を確認する。
  2. ユーザーに対して、今回の変更内容を**「小学生にもわかるように」**噛み砕いて説明する。専門用語を避け、何が変わって何が良くなるのかを伝える。
     - この説明では、変更したファイル名を必ず出す。
     - たとえば `AGENTS.md`、`CLAUDE.md`、`src/App.tsx` のように具体名で説明する。
     - 「案内の紙」「道具」「設定まわり」のような抽象表現だけでまとめない。
     - 説明は必ず **「1行での要約」→「全体像:」→「変更したファイル:」** の順で書く。
     - 最初に**1行での要約**を書く。ここは短く、何をした変更かをひと目でわかる形にする。
     - 次に**全体像:**を書く。「今回は何をそろえたのか」「何のための変更か」を2〜4文で先に伝える。
     - 次に**ファイルごとの説明**を書く。各ファイルについて「どのファイルを」「どう変えたか」「それで何が良くなるか」を書く。
     - 3ファイル以上ある場合も、省略せず、変更したファイル名を全部出す。
     - ユーザーがあとで見返してわかるように、「1行での要約」「全体像」「変更したファイル」を分けて書く。
  3. 作成したコミットメッセージ案（要約＋詳細）を提示する。詳細は**3〜5行**で、短い文に分ける。
  4. 「この内容でコミットして良いですか？」と承認を求める。
- 承認が得られた場合のみ、コミットを実行する。

### コミット前説明の型（必須）

コミット前にユーザーへ説明するときは、できるだけ次の形で書く。

```text
<1行での要約>

全体像:
<この変更が何のためか>
<何がそろうのか、何が良くなるのか>

変更したファイル:
- <ファイル名>: <どのように変えたか>. <どう役立つか>
- <ファイル名>: <どのように変えたか>. <どう役立つか>
- <ファイル名>: <どのように変えたか>. <どう役立つか>
```

### コミット前説明の例（推奨）

```text
Codex CLIをセットアップに追加しました。

全体像:
今回の変更は、私たちがより便利に開発を進めるための道具「Codex CLI」を、パソコンのセットアップ時に自動で準備するようにしたものです。
これまでは手動で入れる必要がありましたが、今回の修正で、最初に一度セットアップスクリプトを動かすだけで、この道具も一緒に用意されます。
また、正しく準備できているかを確認するテスト項目にも追加しました。

変更したファイル:
- setup/setup_mac.sh / setup/setup_windows.ps1: セットアップの中で、Codex CLI を自動で見つけたり入れたりする仕組みを足しました。
- setup/verify_setup.py: セットアップの最後に、この道具がちゃんと使える状態かチェックするようにしました。
- setup/README.md: セットアップで入るものの一覧に Codex CLI を加えました。
- マニュアル/まずはこちらをお読みください.md: 新しく入る道具の説明と、最初に行う認証についての案内を書き足しました。
```

### コミット前説明の見直し（必須）
- 1行での要約が先頭にあるか確認する。
- 全体像だけで終わっていないか確認する。
- ファイル名の一覧だけで終わっていないか確認する。
- 各ファイルについて「何を変えたか」が入っているか確認する。
- 各ファイルについて「それで何が良くなるか」が入っているか確認する。

```bash
git -C "$TEAM_INFO_ROOT" commit -m "<1行要約>

<詳細>"
```

### 4. リモートへの反映 (`git push` / プルリクエスト)
- push の前に、手元の `main` ブランチ上で `git -C "$TEAM_INFO_ROOT" pull --rebase origin main` を行い、リモートの最新状態を取り込む。
- push の前に、必ず `python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" git-lfs-free-plan-status --remote-name origin` を実行する。
- その結果が非 0 なら、push を止める。ユーザーには、無料枠を超える見込みか、無料枠を安全に確認できないため止めたことを、小学生にもわかる言葉で説明する。
- Discord 自動報告を使う場合は、push / PR の前に `git -C "$TEAM_INFO_ROOT" rev-parse origin/main` を実行し、報告用の基点 SHA を控える。

**コンフリクトが発生しなかった場合（または pull が不要だった場合）:**
- オーナー・非オーナー問わず、`main` ブランチへ `git -C "$TEAM_INFO_ROOT" push origin main` を実行して良いか確認し、承認を得てから実行する。
- push 成功後、Discord 自動報告を使う場合は `discord-git-report --event push ...` を実行する。

**コンフリクトが発生した場合（オーナー機ではないとき）:**
- コンフリクトの発生を確認したら、以下の手順で安全のためにプルリクエストに変更する。
- 1. `git -C "$TEAM_INFO_ROOT" rebase --abort` で rebase を取り消し、pull 前の状態に戻す。
- 2. `git -C "$TEAM_INFO_ROOT" config user.name` でアカウント名を取得し、ケバブケースに変換してブランチ名にする（例: `Shoma Deguchi` → `shoma-deguchi`）。
- 3. `git -C "$TEAM_INFO_ROOT" checkout -b <アカウント名ブランチ>`（存在すれば `checkout`）でそのブランチに切り替える。
- 4. `git -C "$TEAM_INFO_ROOT" push -u origin <アカウント名ブランチ>` でプッシュする。
- 5. push 後、必ず `gh pr create` でプルリクエストを作成する。
- 6. PR 作成後、Discord 自動報告を使う場合は `gh pr view --json title,url --jq '.title + "\n" + .url'` などでタイトルと URL を取り、その値を `discord-git-report --event pr ...` に渡して送る。
- ユーザーに「コンフリクトが発生したため、安全のために別ブランチにプッシュしてプルリクエストを作りました。手動でコンフリクトを直してください」と小学生にもわかる言葉で伝える。
- PR のタイトルはコミットメッセージの1行要約を使う。
- **ブランチ名はアカウント名固定。機能名やコミット内容からブランチ名を作ってはいけない。**

**コンフリクトが発生した場合（オーナー機のとき）:**
- ユーザーに「コンフリクトが発生しました。手動でコンフリクトを解決してください」と伝え、解決後に再開できるように待機する。

### 5. マージ・リベース (`git merge`, `git rebase`)
- 実行前に必ずユーザーに確認し、承認を得ること。
- 「なぜマージ/リベースが必要か」を説明する。

## エラー時の対応
- 競合（コンフリクト）が発生した場合は、ユーザーに手動解決を依頼する。


## 注意事項
- コミットメッセージは日本語でも英語でもOK
- プッシュ先は原則として `origin` (team-info) を使用する
- プッシュ時に認証が必要な場合がある（ユーザーにターミナルでの手動実行を依頼）
