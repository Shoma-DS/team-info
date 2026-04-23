import os
import json
import requests
import argparse
import sys

def get_webhook_url():
    """team_info_runtime.py を介して Webhook URL を取得する"""
    try:
        # このスクリプトの場所からリポジトリルートを推測
        # .agent/skills/nanobanana-banner-gen/scripts/discord/banner_batch_report.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
        runtime_script = os.path.join(repo_root, ".agent/skills/common/scripts/team_info_runtime.py")
        
        import subprocess
        result = subprocess.run(
            ["python", runtime_script, "discord-git-webhook-status"],
            capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode == 0:
            line = result.stdout.strip()
            if line.startswith("configured:"):
                # "configured:repo-shared:https://..."
                return line.split(":", 2)[2]
    except Exception as e:
        print(f"Error getting webhook URL: {e}")
    return None

def send_to_discord(payload):
    url = get_webhook_url()
    if not url:
        print("Discord Webhook URL が設定されていません。通知をスキップします。")
        return False
    
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Discord 送信エラー: {e}")
        return False

def format_report(updates, validation_results=None):
    embeds = []
    
    # 1. 生成完了の報告
    if updates:
        fields = []
        for up in updates:
            fields.append({
                "name": up.get("account", "Unknown"),
                "value": f"求人タイプ: {up.get('type', 'Unknown')}\n状態: ✅ 生成・反映完了",
                "inline": True
            })
        
        embeds.append({
            "title": "🍌 Nanobanana バナー生成レポート",
            "color": 0xFEE75C, # Yellow
            "fields": fields,
            "footer": {"text": "Nanobanana Pro Logic"}
        })

    # 2. 検証・整理の報告
    if validation_results:
        summary_text = ""
        ng_items = [r for r in validation_results if r["status"] not in ["OK", "SKIP"]]
        
        if not ng_items:
            summary_text = "✨ すべての画像が正常に配置・整頓されています。"
            status_color = 0x57F287 # Green
        else:
            summary_text = f"⚠️ {len(ng_items)} 件の不整合が見つかり、整理または修復を試みました。"
            status_color = 0xED4245 # Red
            for item in ng_items[:10]: # 最大10件表示
                summary_text += f"\n- [行{item['row']}] {item['account']} ({item['item']}): {item['status']} {item['message']}"
            if len(ng_items) > 10:
                summary_text += f"\n...他 {len(ng_items)-10} 件"

        embeds.append({
            "title": "🔍 Jimoty 画像配置・整合性検証",
            "description": summary_text,
            "color": status_color,
            "footer": {"text": "jmty-image-organizer Logic"}
        })

    return {"embeds": embeds} if embeds else None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="生成結果のJSONデータ")
    parser.add_argument("--validation-json", help="検証結果のJSONデータ")
    args = parser.parse_args()

    updates = json.loads(args.json) if args.json else []
    validation_results = json.loads(args.validation_json) if args.validation_json else None

    payload = format_report(updates, validation_results)
    if payload:
        if send_to_discord(payload):
            print("Discord への通知が完了しました。")
        else:
            print("Discord への通知に失敗しました。")
    else:
        print("通知する内容がありません。")

if __name__ == "__main__":
    main()
