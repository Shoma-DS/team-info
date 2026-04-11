# Discord ロールチェッカースキル

## 概要

Discord サーバーのメンバーとロールを取得し、**Markmap（マインドマップ）形式の Markdown** を自動生成するスキル。

- メンバー別ロール一覧（`members_by_user.md`）
- ロール別メンバー一覧（`members_by_role.md`）
- ポーリングによる変更検知（`--watch` オプション）

---

## スクリプト

| ファイル | 役割 |
|---------|------|
| `scripts/discord/discord_role_report.py` | メイン処理。Markdown生成＋変更検知 |

出力先: `outputs/discord/`

---

## 事前準備（Botトークン取得）

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. **New Application** でアプリを作成
3. 左メニュー「Bot」→「Add Bot」→トークンをコピー
4. 左メニュー「Bot」→ **Privileged Gateway Intents** で以下を ON にする
   - `SERVER MEMBERS INTENT`
5. 左メニュー「OAuth2」→「URL Generator」で以下を設定してBotをサーバーに招待
   - Scopes: `bot`
   - Bot Permissions: `Read Messages/View Channels`（ロール確認のみなら最小権限でOK）

---

## 環境変数の設定

プロジェクトルートの `.env` ファイルに追記（なければ新規作成）:

```
DISCORD_BOT_TOKEN=あなたのBotトークン
DISCORD_GUILD_ID=あなたのサーバーID
```

**サーバーID の確認方法:**
- Discord の設定 → 詳細設定 → 開発者モードを ON
- サーバー名を右クリック →「IDをコピー」

---

## 実行方法

### 一回だけ実行（Markdown生成）

```bash
python "$TEAM_INFO_ROOT/scripts/discord/discord_role_report.py"
```

### 変更を監視しながら定期実行（デフォルト: 5分ごと）

```bash
python "$TEAM_INFO_ROOT/scripts/discord/discord_role_report.py" --watch
```

### 監視間隔を変えたい場合（例: 10分ごと）

```bash
python "$TEAM_INFO_ROOT/scripts/discord/discord_role_report.py" --watch --interval 600
```

---

## 出力ファイル

### `outputs/discord/members_by_user.md`（ユーザー別）

Markmap で開くとユーザーを中心にロールがツリー表示される。

```
# メンバー別ロール一覧
## ニックネーム or アカウント名
### @ロール名
```

### `outputs/discord/members_by_role.md`（ロール別）

ロールを中心にメンバーがツリー表示される。

```
# ロール別メンバー一覧
## @ロール名
### ニックネーム or アカウント名
```

---

## Markmap での表示方法

VS Code の拡張機能 **Markmap**（`gera2ld.markmap-vscode`）で `.md` ファイルを開き、右上のMarkmapアイコンをクリックするとマインドマップが表示される。

---

## AIエージェントへの指示例

- 「Discord のメンバーロール一覧を更新して」→ スクリプトを一回実行
- 「ロールに変更があったら教えて」→ `--watch` モードで起動してもらう
- 「管理者ロールのメンバーを教えて」→ 生成済みの `members_by_role.md` を読む
- 「○○さんのロールを確認して」→ 生成済みの `members_by_user.md` を読む

---

## 注意事項

- Bot に `SERVER MEMBERS INTENT` が有効でないとメンバー一覧が取得できない
- メンバーが1000人を超える場合はページネーションで自動的に全取得する
- `@everyone` ロールは出力から除外している
- `.env` ファイルは `.gitignore` で管理されているので、トークンをコミットしないこと
