#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import argparse
from pathlib import Path

# Webhook Config
REPO_ROOT = Path(__file__).parent.parent.parent
WEBHOOK_CONFIG_PATH = REPO_ROOT / "config" / "discord-git-webhook.json"

def send_discord(content: str):
    """Send message to Discord via Webhook"""
    if not WEBHOOK_CONFIG_PATH.exists():
        print(f"Error: Webhook config not found at {WEBHOOK_CONFIG_PATH}", file=sys.stderr)
        return

    with open(WEBHOOK_CONFIG_PATH, "r") as f:
        webhook_url = json.load(f)["url"]

    data = json.dumps({"content": content}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers=headers
    )
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                print("Discord notification sent.")
            else:
                print(f"Discord API returned status: {response.status}")
    except Exception as e:
        print(f"Failed to send Discord notification: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Send banner update report to Discord")
    parser.add_argument("--account", required=True, help="Account name (e.g. @Sho)")
    parser.add_argument("--type", required=True, choices=["factory", "remote1", "remote2"], help="Image type")
    parser.add_argument("--role-id", help="Discord Role ID to mention (e.g. 123456789)")
    args = parser.parse_args()

    type_map = {
        "factory": "工場求人",
        "remote1": "在宅求人①",
        "remote2": "在宅求人②"
    }
    
    label = type_map.get(args.type, args.type)
    mention = f"<@&{args.role_id}> " if args.role_id else ""
    content = f"{mention}🎨 **バナー画像が更新されました！**\n👤 **対象アカウント**: {args.account}\n🖼️ **変更内容**: {label} のバナーを新しく生成・反映しました。"
    
    send_discord(content)

if __name__ == "__main__":
    main()
