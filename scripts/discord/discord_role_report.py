"""
Discord ロールチェッカー
- メンバー別 / ロール別の Markmap 形式 Markdown を生成
- --watch オプションで変更検知ポーリング
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# python-dotenv がインストールされていれば .env を読み込む
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass  # 環境変数から直接読む

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")

OUTPUT_DIR = Path(__file__).parent.parent.parent / "outputs" / "discord"
SNAPSHOT_FILE = OUTPUT_DIR / ".snapshot.json"

HEADERS = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
BASE_URL = "https://discord.com/api/v10"


# ── API 呼び出し ──────────────────────────────────────────

def get_roles() -> list[dict]:
    """サーバーのロール一覧を取得"""
    url = f"{BASE_URL}/guilds/{DISCORD_GUILD_ID}/roles"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def get_all_members() -> list[dict]:
    """サーバーの全メンバーを取得（1000人超えもページネーション対応）"""
    members = []
    after = "0"
    while True:
        url = f"{BASE_URL}/guilds/{DISCORD_GUILD_ID}/members?limit=1000&after={after}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        members.extend(batch)
        if len(batch) < 1000:
            break
        after = batch[-1]["user"]["id"]
    return members


def get_current_user_guilds() -> list[dict]:
    """Bot から見えている guild 一覧を取得"""
    url = f"{BASE_URL}/users/@me/guilds"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def validate_guild_access():
    """
    設定した guild に Bot が実参加しているかを事前確認する。

    Discord では、UI 上でアプリや連携が見えていても、Bot ユーザー自体が guild に
    参加していない場合がある。その状態で /guilds/{id}/roles を叩くと 403 ではなく
    404 (Unknown Guild) になるため、ここで分かりやすく落とす。
    """
    guilds = get_current_user_guilds()
    guild_map = {guild["id"]: guild["name"] for guild in guilds}
    if DISCORD_GUILD_ID in guild_map:
        return

    visible_guilds = ", ".join(
        f'{guild_id} ({guild_name})'
        for guild_id, guild_name in sorted(guild_map.items(), key=lambda item: item[1].lower())
    ) or "なし"
    raise RuntimeError(
        "設定した DISCORD_GUILD_ID にこの Bot は参加していません。"
        f" 設定値: {DISCORD_GUILD_ID} / Bot から見える guild: {visible_guilds}。"
        " 対象 guild の ID が違うか、アプリは入っていても Bot ユーザーが未招待です。"
    )


# ── データ整形 ────────────────────────────────────────────

def build_role_map(roles: list[dict]) -> dict[str, str]:
    """role_id -> role_name のマップ（@everyone を除外）"""
    return {r["id"]: r["name"] for r in roles if r["name"] != "@everyone"}


def display_name(member: dict) -> str:
    """ニックネーム優先、なければ global_name、なければ username"""
    nick = member.get("nick")
    if nick:
        return nick
    user = member.get("user", {})
    return user.get("global_name") or user.get("username", "不明")


def build_data(members: list[dict], role_map: dict[str, str]):
    """
    Returns:
        user_data: [(display_name, [role_name, ...])]  ロールなしメンバーは除外
        role_data: {role_name: [display_name, ...]}
    """
    user_data = []
    role_data: dict[str, list[str]] = {name: [] for name in role_map.values()}

    for member in members:
        # Bot を除外
        if member.get("user", {}).get("bot"):
            continue

        name = display_name(member)
        roles = [role_map[rid] for rid in member.get("roles", []) if rid in role_map]
        roles_sorted = sorted(roles)

        if roles_sorted:
            user_data.append((name, roles_sorted))

        for role_name in roles_sorted:
            role_data[role_name].append(name)

    user_data.sort(key=lambda x: x[0].lower())
    return user_data, role_data


# ── Markdown 生成 ─────────────────────────────────────────

MARKMAP_FRONTMATTER = """\
---
markmap:
  colorFreezeLevel: 2
  maxWidth: 300
---

"""

def generate_user_md(user_data: list, updated_at: str) -> str:
    lines = [
        MARKMAP_FRONTMATTER,
        f"# メンバー別ロール一覧\n",
        f"## 更新: {updated_at}\n",
    ]
    for name, roles in user_data:
        lines.append(f"\n## {name}\n")
        for role in roles:
            lines.append(f"### @{role}\n")
    return "".join(lines)


def generate_role_md(role_data: dict, updated_at: str) -> str:
    lines = [
        MARKMAP_FRONTMATTER,
        f"# ロール別メンバー一覧\n",
        f"## 更新: {updated_at}\n",
    ]
    for role_name, members in sorted(role_data.items()):
        if not members:
            continue
        lines.append(f"\n## @{role_name}\n")
        for name in sorted(members, key=str.lower):
            lines.append(f"### {name}\n")
    return "".join(lines)


# ── スナップショット（変更検知用）──────────────────────────

def make_snapshot(user_data: list, role_data: dict) -> str:
    """変更検知用のハッシュを生成"""
    data = {"users": user_data, "roles": {k: sorted(v) for k, v in role_data.items()}}
    return hashlib.md5(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def load_snapshot() -> str:
    if SNAPSHOT_FILE.exists():
        return SNAPSHOT_FILE.read_text(encoding="utf-8").strip()
    return ""


def save_snapshot(hash_str: str):
    SNAPSHOT_FILE.write_text(hash_str, encoding="utf-8")


# ── メイン処理 ────────────────────────────────────────────

def run_once(verbose: bool = True) -> bool:
    """
    Markdown を生成する。変更があった場合は True を返す。
    """
    if not DISCORD_BOT_TOKEN or not DISCORD_GUILD_ID:
        print("[エラー] .env に DISCORD_BOT_TOKEN と DISCORD_GUILD_ID を設定してください。")
        sys.exit(1)

    if verbose:
        print("Discord からデータを取得中...")

    validate_guild_access()
    roles = get_roles()
    members = get_all_members()
    role_map = build_role_map(roles)
    user_data, role_data = build_data(members, role_map)

    current_hash = make_snapshot(user_data, role_data)
    previous_hash = load_snapshot()

    if current_hash == previous_hash:
        if verbose:
            print("変更なし。Markdown の更新はスキップしました。")
        return False

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    user_md_path = OUTPUT_DIR / "members_by_user.md"
    role_md_path = OUTPUT_DIR / "members_by_role.md"

    user_md_path.write_text(generate_user_md(user_data, updated_at), encoding="utf-8")
    role_md_path.write_text(generate_role_md(role_data, updated_at), encoding="utf-8")
    save_snapshot(current_hash)

    if verbose:
        print(f"[更新] {user_md_path}")
        print(f"[更新] {role_md_path}")
        print(f"  メンバー数: {len(user_data)} 人")
        print(f"  ロール数: {len([r for r in role_data if role_data[r]])} 種類")

    return True


def run_watch(interval: int):
    """定期的に変更を監視してMarkdownを更新する"""
    print(f"監視モード開始（{interval}秒ごとにチェック）。Ctrl+C で終了。")
    while True:
        try:
            changed = run_once(verbose=True)
            if changed:
                print(f"  → ロール変更を検知しました！Markdownを更新しました。")
            print(f"次のチェック: {interval}秒後 ({datetime.now().strftime('%H:%M:%S')})\n")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n監視を終了しました。")
            break
        except requests.HTTPError as e:
            print(f"[APIエラー] {e}")
            print(f"{interval}秒後に再試行します...")
            time.sleep(interval)


# ── エントリーポイント ─────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Discord ロール一覧を Markdown（Markmap形式）で出力")
    parser.add_argument("--watch", action="store_true", help="変更検知ポーリングモード")
    parser.add_argument("--interval", type=int, default=300, help="ポーリング間隔（秒）デフォルト: 300（5分）")
    args = parser.parse_args()

    if args.watch:
        run_watch(args.interval)
    else:
        run_once()


if __name__ == "__main__":
    main()
