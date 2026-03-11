---
name: team-info-setup
description: team-info の初回セットアップや再セットアップを始めるための起点スキル。既知マシン判定、入口マニュアル確認、setup_all.cmd の実行、TEAM_INFO_ROOT の再登録まで扱う。
---

# team-info セットアップスキル

## 絶対パスルール（必須）
- ユーザーにコマンドを渡すときは、固定の `/Users/...` を使わず、必ず絶対パスで案内する。
- `TEAM_INFO_ROOT` が使えるときは、macOS では `"$TEAM_INFO_ROOT/..."`、Windows では `"$env:TEAM_INFO_ROOT\\..."` の形を優先する。
- 初回セットアップ前で `TEAM_INFO_ROOT` がまだない場合は、`"[team-info を置いた絶対パス]/..."` の形で案内する。
- `cd` と相対パスだけで済ませない。

## 目的
- `/setup` から team-info の初回セットアップややり直しを始める。
- 新しいパソコンか、過去に一度使ったパソコンかを見分ける。
- `setup/setup_all.cmd` を入口にして、必要なら `setup-local-machine` までつなぐ。

## 参照ファイル
- `setup/README.md`
- `マニュアル/まずはこちらをお読みください.md`
- `.agent/skills/common/scripts/team_info_runtime.py`

## 必須フロー
1. まず `python3 .agent/skills/common/scripts/team_info_runtime.py worked-before-status` 相当で状態を確認する。
2. 結果が `new` のときは、最初に `マニュアル/まずはこちらをお読みください.md` を読み、その流れに沿って案内する。
3. 結果が `known` のときは、そのパソコンは既に一度 `team-info` を触った前提で扱う。ユーザーがやり直しを望むなら、そのまま setup を進めてよい。
4. フルセットアップの入口は常に `setup/setup_all.cmd` とする。
   - この入口は OS 別 setup の最後に `setup/verify_setup.py` まで走らせる前提で扱う。
   - `Verify status: passed` かつ終了コード 0 のときだけ「環境がそろった」と判断する。
5. setup 完了後は、ターミナルを開き直して `TEAM_INFO_ROOT` を確認するよう案内する。
   - macOS は `~/.config/team-info/env.sh` と `launchctl` に保存される前提で扱う。
6. `TEAM_INFO_ROOT` が空なら、`setup-local-machine` で作業場所だけを登録し直す。
7. 新しいパソコンで setup が終わったら、もう一度 `マニュアル/まずはこちらをお読みください.md` を読むよう促す。
8. それでも止まる場合は、止まった画面のスクリーンショットを添えて Discord `https://discord.com/channels/1478351976168165511/1479287635535990794` へ相談するよう案内する。

## ユーザー向けコマンド

### 初回セットアップの入口

macOS:

```bash
bash ./setup/setup_all.cmd
```

Windows:

```powershell
.\setup\setup_all.cmd
```

- この最初のコマンドだけは、`team-info` のリポジトリルートをカレントディレクトリにした状態で案内してよい。
- setup 側はカレントディレクトリが repo root なら、その値を `TEAM_INFO_ROOT` として保存する。

### `TEAM_INFO_ROOT` が設定済みのときの再セットアップ

macOS:

```bash
bash "$TEAM_INFO_ROOT/setup/setup_all.cmd"
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\setup\setup_all.cmd"
```

### `TEAM_INFO_ROOT` の確認

macOS:

```bash
echo "$TEAM_INFO_ROOT"
```

Windows:

```powershell
echo $env:TEAM_INFO_ROOT
```

### 作業場所だけを登録し直す

macOS:

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" setup-local-machine --repo-root "$TEAM_INFO_ROOT"
```

Windows:

```powershell
py -3 "$env:TEAM_INFO_ROOT\.agent\skills\common\scripts\team_info_runtime.py" setup-local-machine --repo-root "$env:TEAM_INFO_ROOT" --shell powershell
```

- このパソコンをオーナー機として使うときだけ、最後に `--owner` を付ける。

### Docker サービスを起動する

セットアップ後に `Dify` や `n8n` を起動するときは、素の `docker compose up` ではなく共通ランチャーを使う。

macOS:

```bash
bash "$TEAM_INFO_ROOT/run.sh" --project dify -d
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project dify -d
```

- `n8n` を起動したいときは `dify` を `n8n` に置き換える。
- このランチャーが Docker Desktop の有無確認、起動、Engine 待機まで面倒を見る。

## 承認ルール
- `worked-before-status` の確認やマニュアルの読み込みは、そのまま実行してよい。
- `setup/setup_all.cmd` の実行は、道具の追加、外部取得、環境変更を含むため、必ず日本語で承認を取り、リスクを数値で示してから進める。
- ユーザーが自分で実行したい場合は、上のコマンドをそのまま渡す。
