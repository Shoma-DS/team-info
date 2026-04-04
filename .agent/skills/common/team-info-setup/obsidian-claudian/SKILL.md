---
name: obsidian-claudian
description: official Obsidian CLI と Claudian を team-info 向けに導入・更新する。アクティブ vault の plugin 配備、`.claude/claudian-settings.json` の初期化、初期 subagent 雛形の seed まで行う。
---

# obsidian-claudian スキル

## 役割
- official Obsidian CLI と Claudian を、今のマシンとアクティブ vault に合わせて導入する。
- Claudian plugin を vault に配備し、日本語 UI、`~/.claude` 読み込み、Claude CLI パス、添付フォルダ整合を最小構成で整える。
- repo には再利用できる installer / doctor を残し、runtime の設定は vault 側へ閉じ込める。

## 保存先
- Obsidian app: `/Applications/Obsidian.app`
- official Obsidian CLI: `/usr/local/bin/obsidian`
- Claudian plugin: `<vault>/.obsidian/plugins/claudian/`
- Claudian settings: `<vault>/.claude/claudian-settings.json`
- 初期 subagent 雛形: `<vault>/.claude/agents/`

## 導入手順
1. 公式 Obsidian を 1.12 系以上で入れる。
2. `obsidian` CLI が見えることを確認する。
3. Claudian plugin を active vault に配備する。
4. `.claude/claudian-settings.json` を最小構成で初期化する。

## 初回導入

```bash
"$(command -v brew)" install --cask obsidian
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" install --skip-if-no-vault
```

## 状態確認

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" doctor
```

## team-info 優先ルール
- repo の正本はこの `SKILL.md` と `scripts/` 配下。vault 側の `.claude/` は runtime 設定として扱う。
- Claudian の `permissionMode` は初期値を `normal` にする。いきなり `yolo` へはしない。
- `loadUserClaudeSettings` は有効のままにし、既存の `~/.claude/settings.json` を活かす。
- 添付フォルダは vault の `.obsidian/app.json` を読み、root 保存なら Claudian 側は空文字のままにする。
- upstream の plugin build 手順は残すが、通常導入は release asset 取得を優先する。

## install がやること
- `~/Library/Application Support/obsidian/obsidian.json` から active vault を見つける
- `~/Library/Application Support/obsidian/obsidian.json` に `cli: true` を反映する
- latest Claudian release の `main.js` / `manifest.json` / `styles.css` を取得する
- active vault の `.obsidian/plugins/claudian/` に配置する
- `.obsidian/community-plugins.json` に `claudian` を追加する
- `.claude/claudian-settings.json` に以下を反映する
  - `locale: "ja"`
  - `permissionMode: "normal"`
  - `loadUserClaudeSettings: true`
  - `claudeCliPathsByHost[<hostname>] = <detected claude path>`
  - `mediaFolder = <vault attachment folder>`
- `.claude/agents/` に次の初期雛形を必要時だけ seed する
  - `note-summarizer.md`
  - `file-organizer.md`

## よく使うコマンド

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" doctor
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" install --skip-if-no-vault
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" install --vault "/absolute/path/to/vault" --user-name "Shouma"
```

## 導入後の確認
- Obsidian を再起動し、Community plugins で `Claudian` が有効になっているか確認する
- `obsidian version` が通らない場合は、Obsidian 再起動後にもう一度試す
- Claudian Settings で表示言語が日本語か確認する
- `Safe` 相当で始めたい場合は `permissionMode: normal` のままで運用する
- 画像/PDF を読む vault では、添付保存先と Claudian `mediaFolder` の整合だけ崩さない
- 初期 subagent は seed 済みでも上書きしない。既存の `.claude/agents/*.md` を優先する
