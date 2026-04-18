#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import argparse
from pathlib import Path
from collections import defaultdict

# Config
REPO_ROOT = Path(__file__).parent.parent.parent
WEBHOOK_CONFIG_PATH = REPO_ROOT / "config" / "discord-banner-webhook.json"
ROLE_ID = "1479038295345463411"
DISCORD_CHAR_LIMIT = 1950  # Slightly less than 2000 for safety

TYPE_MAP = {
    "factory": "工場求人",
    "remote1": "在宅求人①",
    "remote2": "在宅求人②"
}

def send_discord(content: str):
    if not WEBHOOK_CONFIG_PATH.exists():
        print(f"Error: Webhook config not found at {WEBHOOK_CONFIG_PATH}", file=sys.stderr)
        return

    with open(WEBHOOK_CONFIG_PATH, "r") as f:
        webhook_url = json.load(f)["url"]

    data = json.dumps({
        "content": content,
        "allowed_mentions": {"roles": [ROLE_ID]}
    }).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    req = urllib.request.Request(webhook_url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                print("Discord notification sent.")
            else:
                print(f"Discord API returned status: {response.status}")
    except Exception as e:
        print(f"Failed to send Discord notification: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Send consolidated banner update report to Discord")
    parser.add_argument("--json", required=True, help='JSON string like [{"account": "@Sho", "type": "factory"}, ...]')
    args = parser.parse_args()

    try:
        updates = json.loads(args.json)
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)

    # Grouping
    grouped = defaultdict(list)
    for item in updates:
        grouped[item["account"]].append(TYPE_MAP.get(item["type"], item["type"]))

    # Build Message
    header = f"<@&{ROLE_ID}>\n🎨 **バナー画像の生成・反映が完了しました！**\n"
    blocks = []
    
    for account, types in grouped.items():
        block = f"\n---\n👤 **{account}**\n"
        for t in sorted(set(types)):
            block += f"・{t}\n"
        blocks.append(block)

    # Split logic
    current_message = header
    for block in blocks:
        if len(current_message) + len(block) > DISCORD_CHAR_LIMIT:
            send_discord(current_message)
            current_message = "（続き）\n" + block
        else:
            current_message += block
    
    if current_message:
        send_discord(current_message)

if __name__ == "__main__":
    main()
