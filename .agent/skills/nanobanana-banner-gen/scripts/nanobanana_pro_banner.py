import os
import json
import subprocess
import argparse

SPREADSHEET_ID = "1GKBTHwBS6W0D30X_yK7vqsaDRWw3p1tXM7lnFhyb0Uw"
SHEET_NAME = "アカウント情報"
DRIVE_OUTPUT_FOLDER = "outputs/nanobanana"

def run_gws_command(cmd_args):
    """gws CLIコマンドを実行し、結果をJSON形式で受け取る"""
    cmd = ["gws"] + cmd_args
    # Windowsで動かした際、エンコードエラー等を避けるために utf-8 を指定
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"GWS error:\n{result.stderr}")
    return json.loads(result.stdout) if result.stdout.strip() else None

def get_sheet_values(range_a1):
    """スプレッドシートの指定範囲を取得する"""
    try:
        data = run_gws_command(["sheets", "spreadsheets", "values", "get", "--params", json.dumps({
            "spreadsheetId": SPREADSHEET_ID,
            "range": range_a1
        })])
        return data.get("values", [])
    except Exception as e:
        print(f"Error reading {range_a1}: {e}")
        return []

def update_sheet_values(range_a1, values):
    """スプレッドシートの指定セル群を更新する"""
    data = run_gws_command(["sheets", "spreadsheets", "values", "update", "--params", json.dumps({
        "spreadsheetId": SPREADSHEET_ID,
        "range": range_a1,
        "valueInputOption": "USER_ENTERED"
    }), "--json", json.dumps({
        "values": values
    })])
    return data

def upload_image_to_drive(file_path):
    """画像をGoogle Driveにアップロードし、閲覧権限を付与してファイルIDを返す"""
    params = {"name": os.path.basename(file_path)}
    
    # 1. Driveへアップロード
    res = run_gws_command([
        "drive", "files", "create",
        "--upload", file_path,
        "--params", json.dumps(params)
    ])
    file_id = res["id"]
    
    # 2. 誰でも閲覧可能(reader)な権限を付与 (IMAGE() 関数で読み込ませるため必須)
    run_gws_command([
        "drive", "permissions", "create",
        "--params", json.dumps({
            "fileId": file_id
        }),
        "--json", json.dumps({
            "role": "reader",
            "type": "anyone"
        })
    ])
    
    return file_id

def generate_banner(prompt_text, output_file):
    """
    Nanobanana Pro (Gemini 3 Pro Image) を用いてバナーを生成するモック関数
    実際にはここに Google GenAI API の画像生成コードを組み込みます。
    """
    print(f"  [Nanobanana Pro] 画像生成を実行中...\n  -> プロンプト: {prompt_text[:20]}...\n  -> 出力先: {output_file}")
    
    # MOCK: Pillow を使ってダミー画像を生成
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (1024, 1024), color=(255, 220, 100))
        d = ImageDraw.Draw(img)
        d.text((100, 500), f"AUTO GENERATED BANNER\nMocked Nanobanana Pro\n{prompt_text[:30]}", fill=(0, 0, 0))
        img.save(output_file)
    except ImportError:
        # Pillowが無い環境向けのダミーファイル出力
        with open(output_file, "w") as f:
            f.write("dummy image content")

    print("  ✓ バナー生成完了")
    return output_file

def process_accounts(target_type):
    print(f"=== {target_type}用バナーの一括生成処理を開始します ===")
    
    if target_type == "工場":
        # 読み出し列: G(インデックス6) または M(インデックス12)
        content_cols = [6, 12]
        # 更新する列: I列
        image_col = "I"
    elif target_type == "在宅":
        # 読み出し列: S(インデックス18) または U(インデックス20)
        content_cols = [18, 20]
        # 更新する列: RまたはT (ここではR列を優先)
        image_col = "R"
    else:
        print("未対応の対象です")
        return
        
    os.makedirs(DRIVE_OUTPUT_FOLDER, exist_ok=True)
    
    # 2行目以降のデータを取得
    range_query = f"{SHEET_NAME}!A2:Z"
    rows = get_sheet_values(range_query)
    
    if not rows:
        print("データがありませんでした。")
        return
        
    for i, row in enumerate(rows):
        row_idx = i + 2 # スプレッドシートは1-indexed表記、かつA2から読み取っているので
        
        # 投稿文を取得
        post_text = ""
        for col_idx in content_cols:
            if col_idx < len(row) and row[col_idx].strip():
                post_text = row[col_idx].strip()
                break
                
        if not post_text:
            continue # 投稿文が空の場合はスキップ
            
        print(f"\n[行 {row_idx}] 投稿文を検知しました。バナー生成処理に入ります。")
        output_filename = os.path.join(DRIVE_OUTPUT_FOLDER, f"{target_type}_banner_row{row_idx}.jpg")
        
        # バナー画像（正方形）の生成
        generate_banner(post_text, output_filename)
        
        # Google Driveへのアップロード
        print("  Driveへアップロードし、権限を付与しています...")
        file_id = upload_image_to_drive(output_filename)
        
        # シートへの書き込み (=IMAGE 関数)
        image_formula = f'=IMAGE("https://drive.google.com/uc?id={file_id}")'
        update_range = f"{SHEET_NAME}!{image_col}{row_idx}"
        
        print(f"  シートを更新中 ({update_range})...")
        update_sheet_values(update_range, [[image_formula]])
        
        print(f"  ✓ 行 {row_idx} の処理がすべて完了しました！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nanobanana Pro Banner Generator for Spreadsheet")
    parser.add_argument("--type", choices=["both", "factory", "remote"], default="factory", 
                        help="生成対象を指定: factory(工場), remote(在宅), both(両方)")
    args = parser.parse_args()
    
    if args.type in ["factory", "both"]:
        process_accounts("工場")
    if args.type in ["remote", "both"]:
        process_accounts("在宅")
