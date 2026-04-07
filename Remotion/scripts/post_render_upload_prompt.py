import os
import argparse
import sys
import json
import datetime
from pathlib import Path

def get_video_description(video_path):
    """
    Tries to find a matching .md description file in the outputs directory.
    Example: outputs/acoriel/renders/Hana.mp4 -> outputs/acoriel/descriptions/Hana_Orange_Range.md
    """
    video_path = Path(video_path)
    video_name = video_path.stem # e.g. "Hana"
    
    # Common locations for descriptions
    root_dir = Path(__file__).parent.parent.parent.parent.parent.parent
    desc_dir = root_dir / "outputs" / "acoriel" / "descriptions"
    
    if not desc_dir.exists():
        return None, None
    
    # Try exact match or prefix match
    for f in desc_dir.glob("*.md"):
        if video_name.lower() in f.name.lower():
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                # Use the first line as title, the rest as description
                lines = content.split('\n')
                title = lines[0].strip()
                description = '\n'.join(lines[1:]).strip()
                return title, description
                
    return None, None

def prompt_user():
    print("\n" + "="*40)
    print("🎬  Render Completed!")
    print("="*40)
    
    choice = input("\nYouTubeにアップロードしますか？ [y/N]: ").lower()
    if choice != 'y':
        print("アップロードをスキップします。")
        return None

    # Account selection
    accounts = ['acoriel', 'sleep_travel', 'other']
    print("\nアカウントを選択してください:")
    for i, acc in enumerate(accounts, 1):
        print(f"{i}. {acc}")
    
    acc_idx = input(f"番号を入力してください [1-{len(accounts)}]: ")
    try:
        account = accounts[int(acc_idx)-1]
        if account == 'other':
            account = input("アカウント名を入力してください: ")
    except:
        account = 'acoriel'

    # Privacy selection
    privacies = ['public', 'unlisted', 'private']
    print("\n公開設定を選択してください:")
    for i, priv in enumerate(privacies, 1):
        print(f"{i}. {priv}")
    
    priv_idx = input(f"番号を入力してください [1-{len(privacies)}]: ")
    try:
        privacy = privacies[int(priv_idx)-1]
    except:
        privacy = 'unlisted'

    # Scheduling
    publish_at = None
    if privacy != 'unlisted':
        sched_choice = input("\n公開予約をしますか？ [y/N]: ").lower()
        if sched_choice == 'y':
            print("\n予約日時を入力してください (例: 2024-04-10 18:00)")
            print("形式: YYYY-MM-DD HH:MM")
            date_str = input("日時: ")
            try:
                # Convert to ISO 8601 for YouTube API (UTC)
                # Note: Currently assumes local time and converts to UTC. 
                # For simplicity in this demo, we'll just format it.
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                # YouTube API needs 'Z' suffix for UTC or offset
                publish_at = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                privacy = 'private' # Scheduled videos must be private initially
            except:
                print("❌ 無効な日時形式です。即時公開（または非公開）として扱います。")

    return {
        "account": account,
        "privacy": privacy,
        "publish_at": publish_at
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to rendered video file")
    args = parser.parse_args()

    title, description = get_video_description(args.file)
    if not title:
        title = Path(args.file).stem
        description = "Acoriel Acoustic Cover"

    upload_config = prompt_user()
    if upload_config:
        # Prepare command
        uploader_script = Path(__file__).parent.parent / ".agent" / "skills" / "common" / "youtube-auto-upload" / "scripts" / "youtube_uploader.py"
        
        cmd = [
            "python3",
            f"\"{uploader_script}\"",
            "--file", f"\"{args.file}\"",
            "--account", upload_config["account"],
            "--title", f"\"{title}\"",
            "--description", f"\"{description}\"",
            "--privacy", upload_config["privacy"]
        ]
        
        if upload_config["publish_at"]:
            cmd.extend(["--publish-at", upload_config["publish_at"]])
            
        print("\n🚀 以下のコマンドを実行します:")
        print(" ".join(cmd))
        
        # Execute (or provide to user to execute since it might need browser)
        print("\n(ブラウザ認証が必要になる場合があるため、以下のコマンドをコピーして実行してください)")
        print("\n" + " ".join(cmd) + "\n")
