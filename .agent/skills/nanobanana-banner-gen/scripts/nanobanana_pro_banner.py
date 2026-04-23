import os
import json
import subprocess
import argparse
import random
import re
import sys
import base64
import time
import requests

# Constants
SPREADSHEET_ID = "1GKBTHwBS6W0D30X_yK7vqsaDRWw3p1tXM7lnFhyb0Uw"
SHEET_NAME = "アカウント情報"
DRIVE_OUTPUT_FOLDER = "outputs/nanobanana"
TASK_DIR = os.path.join(".agent", "skills", "nanobanana-banner-gen", "tasks")
PARENT_FOLDER_ID = "16P5sOzyJHLemwURON6Wf1i7NjodK3WWF"
PROMPT_DIR = os.path.join(".agent", "skills", "nanobanana-banner-gen", "prompts")

# Mapping for target columns: (Read Index, Write Column, Label, TypeKey)
COL_MAPPING = [
    (9, "I", "Factory", "factory"),    # J -> I
    (18, "R", "Remote1", "remote1"),  # S -> R
    (20, "T", "Remote2", "remote2")   # U -> T
]

def load_env():
    """Simple .env parser to get GEMINI_API_KEY"""
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("GEMINI_API_KEY")

def run_gws_command(cmd_args):
    """gws CLIコマンドを実行し、結果をJSON形式で受け取る"""
    cmd = ["gws.cmd"] + cmd_args
    # Windows/PowerShell compatibility: ensure encoding
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"GWS error:\n{result.stderr}")
    return json.loads(result.stdout) if result.stdout.strip() else None

def get_sheet_values(range_a1):
    """スプレッドシートの指定範囲を取得する"""
    try:
        data = run_gws_command(["sheets", "spreadsheets", "values", "get", "--params", json.dumps({
            "spreadsheetId": SPREADSHEET_ID,
            "range": range_a1,
            "valueRenderOption": "FORMULA"
        })])
        return data.get("values", [])
    except Exception as e:
        print(f"Error reading {range_a1}: {e}")
        return []

def upload_image_to_drive(file_path, parent_id):
    """画像をGoogle Driveにアップロードし、閲覧権限を付与してファイルIDを返す"""
    params = {
        "name": os.path.basename(file_path),
        "parents": [parent_id]
    }
    
    res = run_gws_command([
        "drive", "files", "create",
        "--upload", file_path,
        "--params", json.dumps(params)
    ])
    file_id = res["id"]
    
    run_gws_command([
        "drive", "permissions", "create",
        "--params", json.dumps({"fileId": file_id}),
        "--json", json.dumps({"role": "reader", "type": "anyone"})
    ])
    
    return file_id

def get_or_create_account_folder(account_name):
    """アカウント名に紐づくフォルダIDを取得または作成する"""
    if not account_name:
        account_name = "Unknown"
        
    query = f"'{PARENT_FOLDER_ID}' in parents and name = '{account_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    res = run_gws_command(["drive", "files", "list", "--params", json.dumps({"q": query})])
    
    if res and "files" in res and len(res["files"]) > 0:
        return res["files"][0]["id"]
    
    print(f"  フォルダ '{account_name}' を作成中...")
    res = run_gws_command(["drive", "files", "create", "--params", json.dumps({
        "resource": {
            "name": account_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [PARENT_FOLDER_ID]
        }
    })])
    return res["id"]

def export_tasks(specific_row=None, force_overwrite=False):
    """スプレッドシートから未処理の行を抽出してローカルのtasksフォルダに書き出す"""
    print(f"=== タスク書き出しを開始します (Row: {specific_row if specific_row else 'All'}) ===")
    os.makedirs(TASK_DIR, exist_ok=True)
    
    # Clear existing tasks
    for f in os.listdir(TASK_DIR):
        if f.startswith("task_"):
            os.remove(os.path.join(TASK_DIR, f))

    range_query = f"{SHEET_NAME}!A7:Z"
    rows = get_sheet_values(range_query)
    
    if not rows:
        print("データがありませんでした。")
        return
        
    tasks_count = 0
    for i, row in enumerate(rows):
        row_idx = i + 7
        if specific_row and row_idx != specific_row:
            continue
            
        account_name = row[1].strip() if len(row) > 1 else ""
        if not account_name: continue
        
        for read_idx, write_col, label, type_key in COL_MAPPING:
            # ジョブテキスト
            if read_idx >= len(row) or not str(row[read_idx]).strip():
                continue
            
            # すでに画像があるかチェック
            write_idx = ord(write_col) - ord('A')
            if not force_overwrite and write_idx < len(row) and "IMAGE" in str(row[write_idx]):
                continue
                
            job_text = str(row[read_idx]).strip()
            task_id = f"{row_idx:02d}_{type_key}"
            
            task_data = {
                "task_id": task_id,
                "row_idx": row_idx,
                "account_name": account_name,
                "type": type_key,
                "label": label,
                "read_col": chr(ord('A') + read_idx),
                "write_col": write_col,
                "status": "pending"
            }
            
            # JSON 保存
            with open(os.path.join(TASK_DIR, f"task_{task_id}.json"), "w", encoding="utf-8") as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
            
            # TEXT 保存 (AIが読み書きしやすいように)
            with open(os.path.join(TASK_DIR, f"task_{task_id}.txt"), "w", encoding="utf-8") as f:
                f.write(job_text)
            
            tasks_count += 1
            print(f"  [EXPORTED] Task {task_id} for {account_name}")

    print(f"\n✅ {tasks_count} 件のタスクを書き出しました。ディレクトリ: {TASK_DIR}")

def call_gemini_imagen_api(prompt, output_path):
    """Gemini API (Imagen 3) を直接叩いて画像を生成する"""
    api_key = load_env()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env or environment.")

    # Imagen 3.0 API endpoint for AI Studio
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
    
    payload = {
        "instances": [
            {"prompt": prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "outputMimeType": "image/jpeg"
        }
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code != 200:
        try:
            err_msg = response.json().get("error", {}).get("message", response.text)
        except:
            err_msg = response.text
        raise RuntimeError(f"API Error ({response.status_code}): {err_msg}")

    data = response.json()
    predictions = data.get("predictions", [])
    if not predictions:
        raise RuntimeError(f"No predictions returned from API: {response.text}")

    b64_data = predictions[0].get("bytesBase64Encoded")
    if not b64_data:
        raise RuntimeError("No image data found in prediction.")

    with open(output_path, "wb") as f:
        f.write(base64.b64decode(b64_data))
    
    return output_path

def generate_task_image(task_id):
    """特定のタスクIDに対してAPIキーを使って画像生成を実行する"""
    json_path = os.path.join(TASK_DIR, f"task_{task_id}.json")
    txt_path = os.path.join(TASK_DIR, f"task_{task_id}.txt")
    
    if not os.path.exists(json_path) or not os.path.exists(txt_path):
        print(f"Error: Task files for {task_id} not found.")
        return False

    with open(json_path, "r", encoding="utf-8") as f:
        task = json.load(f)
    with open(txt_path, "r", encoding="utf-8") as f:
        job_text = f.read()

    print(f"  [API MODE] Generating image for Task {task_id}...")
    
    # Simple Prompt
    prompt = f"{job_text}\n\nHigh quality job banner design, professional typography, square 1:1."

    os.makedirs(DRIVE_OUTPUT_FOLDER, exist_ok=True)
    output_filename = os.path.join(DRIVE_OUTPUT_FOLDER, f"{task['label']}_Job_{task['row_idx']:02d}.jpg")
    
    try:
        call_gemini_imagen_api(prompt, output_filename)
        print(f"  ✅ Generated: {output_filename}")
        return True
    except Exception as e:
        print(f"  ❌ API Generation Failed: {e}")
        return False

def import_results():
    """生成された画像をGoogle Driveにアップロードし、スプレッドシートに一括反映する"""
    print(f"=== 結果のインポートを開始します ===")
    if not os.path.exists(TASK_DIR):
        print("Error: tasks directory not found.")
        return []

    task_files = [f for f in os.listdir(TASK_DIR) if f.endswith(".json")]
    if not task_files:
        print("処理すべきタスクがありません。先ずは export を実行してください。")
        return []

    os.makedirs(DRIVE_OUTPUT_FOLDER, exist_ok=True)
    update_results = []
    batch_updates = []

    processed_tasks = []
    for task_file in sorted(task_files):
        with open(os.path.join(TASK_DIR, task_file), "r", encoding="utf-8") as f:
            task = json.load(f)
        
        task_id = task["task_id"]
        # 画像ファイルを探す
        img_path = os.path.join(DRIVE_OUTPUT_FOLDER, f"{task['label']}_Job_{task['row_idx']:02d}.jpg")
        if not os.path.exists(img_path):
            print(f"⚠️ 画像が見つかりません。スキップします: {img_path}")
            continue

        print(f"\n[{task_id}] アップロード中: {task['account_name']} ({task['type']})")
        
        try:
            # フォルダ取得
            folder_id = get_or_create_account_folder(task["account_name"])
            # アップロード
            file_id = upload_image_to_drive(img_path, folder_id)
            
            # 反映用の式
            image_formula = f'=IMAGE("https://drive.google.com/uc?id={file_id}")'
            batch_updates.append({
                "range": f"{SHEET_NAME}!{task['write_col']}{task['row_idx']}",
                "values": [[image_formula]]
            })
            
            update_results.append({"account": task["account_name"], "type": task["type"]})
            processed_tasks.append(task_file) # Track success
        except Exception as e:
            print(f"❌ エラー発生 ({task_id}): {e}")

    if batch_updates:
        print(f"\n📊 {len(batch_updates)} 件のスプレッドシート一括更新を実行中...")
        payload = {
            "valueInputOption": "USER_ENTERED",
            "data": batch_updates
        }
        run_gws_command([
            "sheets", "spreadsheets", "values", "batchUpdate",
            "--params", json.dumps({"spreadsheetId": SPREADSHEET_ID}),
            "--json", json.dumps(payload)
        ])
        print("✅ スプレッドシートの更新が完了しました。")
        
        # 完了したタスクファイルのみを削除
        for task_file in processed_tasks:
            os.remove(os.path.join(TASK_DIR, task_file))
            txt_file = task_file.replace(".json", ".txt")
            if os.path.exists(os.path.join(TASK_DIR, txt_file)):
                os.remove(os.path.join(TASK_DIR, txt_file))
    else:
        print("反映すべき項目はありませんでした。")
    
    return update_results

def run_post_process_validation(update_results):
    """後処理（整理、検証、Discord通知）を実行する"""
    print("\n--- 自動検証と整理を開始します (jmty-image-organizer) ---")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 1. 整理の実行
        organize_script = os.path.abspath(os.path.join(current_dir, "../../jmty/jmty-image-organizer/scripts/organize_images.py"))
        if os.path.exists(organize_script):
            print(f"Running organizer: {organize_script}")
            subprocess.run(["python", organize_script], check=True)
        
        # 2. 検証結果の取得
        investigate_script = os.path.abspath(os.path.join(current_dir, "../../jmty/jmty-image-organizer/scripts/investigate_spreadsheet.py"))
        if os.path.exists(investigate_script):
            print(f"Running investigator: {investigate_script}")
            subprocess.run(["python", investigate_script], check=True)
        
        # 3. Discord 通知
        report_script = os.path.abspath(os.path.join(current_dir, "discord/banner_batch_report.py"))
        if os.path.exists(report_script):
            print("\n--- Discord 通知を送信します ---")
            report_cmd = ["python", report_script]
            if update_results:
                report_cmd += ["--json", json.dumps(update_results)]
            
            # investigation_result.json を探す
            repo_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))
            json_path = os.path.join(repo_root, "investigation_result.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    v_res = json.load(f)
                    report_cmd += ["--validation-json", json.dumps(v_res)]
            
            subprocess.run(report_cmd)
            
    except Exception as e:
        print(f"後処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # Ensure UTF-8 output for Windows console
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            # Fallback for older python, though reconfigure is best
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description="Nanobanana Pro Task-Based Bulk Banner Generator")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export tasks from spreadsheet to local files")
    export_parser.add_argument("--row", type=int, help="Specific row to export")
    export_parser.add_argument("--force", action="store_true", help="Force export even if image exists")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import generated images back to Drive/Sheets")
    import_parser.add_argument("--no-report", action="store_true", help="Skip post-process report")

    # Generate command (API Mode)
    generate_parser = subparsers.add_parser("generate", help="Generate image using Gemini API for a task")
    generate_parser.add_argument("--task_id", required=True, help="Task ID to generate (e.g. 07_factory)")

    args = parser.parse_args()
    
    if args.command == "export":
        export_tasks(args.row, args.force)
    elif args.command == "import":
        updates = import_results()
        if not args.no_report:
            run_post_process_validation(updates)
    elif args.command == "generate":
        generate_task_image(args.task_id)
    else:
        parser.print_help()
