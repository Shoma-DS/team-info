import requests
import json
import os
import glob
from typing import Dict, Any, List
import datetime

# VOICEVOXエンジンのAPIエンドポイント
VOICEVOX_API_BASE_URL = "http://127.0.0.1:50021"

# フォルダパス (チームインフォのルートからの相対パス)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Remotionディレクトリ
SCRIPT_DIR = os.path.join(BASE_DIR, "scripts", "voice_scripts")
CONFIG_FILE = os.path.join(BASE_DIR, "configs", "voice_config.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "audio")

def load_voice_config() -> Dict[str, Any]:
    """Voicebox設定ファイルを読み込む"""
    if not os.path.exists(CONFIG_FILE):
        print(f"エラー: 設定ファイルが見つかりません: {CONFIG_FILE}")
        return {{}}
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_available_scripts() -> List[str]:
    """台本フォルダ内の利用可能なスクリプトファイル (.txt, .md) を取得する"""
    script_files = glob.glob(os.path.join(SCRIPT_DIR, "*.txt")) + \
                   glob.glob(os.path.join(SCRIPT_DIR, "*.md"))
    return [os.path.basename(f) for f in script_files]

def select_script_file(available_scripts: List[str]) -> str:
    """ユーザーに台本ファイルを選択させる"""
    if not available_scripts:
        print(f"エラー: '{SCRIPT_DIR}' フォルダに台本ファイルが見つかりません (.txt または .md 形式)。")
        return ""

    print("\n--- 利用可能な台本ファイル ---")
    for i, script_name in enumerate(available_scripts):
        print(f"{i+1}: {script_name}")

    while True:
        try:
            choice = int(input("使用する台本ファイルの番号を選択してください: "))
            if 1 <= choice <= len(available_scripts):
                return available_scripts[choice-1]
            else:
                print("無効な番号です。再度入力してください。")
        except ValueError:
            print("無効な入力です。番号で入力してください。")

def select_voice_profile(voice_configs: Dict[str, Any]) -> str:
    """ユーザーに音声設定プロファイルを選択させる"""
    if not voice_configs:
        print("エラー: 音声設定プロファイルがありません。")
        return ""

    print("\n--- 利用可能な音声設定プロファイル ---")
    profile_names = list(voice_configs.keys())
    for i, profile_name in enumerate(profile_names):
        print(f"{i+1}: {profile_name}")

    while True:
        try:
            choice = int(input("使用する音声設定プロファイルの番号を選択してください: "))
            if 1 <= choice <= len(profile_names):
                return profile_names[choice-1]
            else:
                print("無効な番号です。再度入力してください。")
        except ValueError:
            print("無効な入力です。番号で入力してください。")

def get_voicevox_speakers() -> Dict[str, Dict[str, int]]:
    """VOICEVOXエンジンから利用可能なスピーカー情報を取得し、整形する"""
    try:
        response = requests.get(f"{VOICEVOX_API_BASE_URL}/speakers")
        response.raise_for_status()
        raw_speakers_data = response.json()

        # speaker_name -> style_name -> speaker_id の形式に整形
        speaker_map = {}
        for speaker_data in raw_speakers_data:
            speaker_name = speaker_data['name']
            speaker_map[speaker_name] = {}
            for style in speaker_data['styles']:
                style_name = style['name']
                speaker_id = style['id']
                speaker_map[speaker_name][style_name] = speaker_id
        return speaker_map
    except requests.exceptions.ConnectionError:
        print(f"エラー: VOICEVOXエンジンに接続できませんでした。'{VOICEVOX_API_BASE_URL}' が起動しているか確認してください。")
        return {}
    except requests.exceptions.RequestException as e:
        print(f"VOICEVOXスピーカー情報の取得中にエラーが発生しました: {e}")
        return {}

def generate_audio_query(text: str, speaker_id: int, speed: float = 1.0, pitch: float = 0.0) -> Dict[str, Any]:
    """音声合成クエリを生成する"""
    params = {
        "text": text,
        "speaker": speaker_id,
    }
    try:
        response = requests.post(f"{VOICEVOX_API_BASE_URL}/audio_query", params=params)
        response.raise_for_status()
        query = response.json()
        
        # speedとpitchをクエリに適用
        query["speedScale"] = speed
        query["pitchScale"] = pitch
        return query
    except requests.exceptions.RequestException as e:
        print(f"音声クエリの生成中にエラーが発生しました: {e}")
        return {{}}

def synthesize_voice(speaker_id: int, audio_query: Dict[str, Any]) -> bytes:
    """音声を合成する"""
    params = {
        "speaker": speaker_id,
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            f"{VOICEVOX_API_BASE_URL}/synthesis",
            params=params,
            headers=headers,
            data=json.dumps(audio_query)
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"音声合成中にエラーが発生しました: {e}")
        return b""

def main():
    print("VOICEVOX自動音声生成スキルを開始します。")

    # VOICEVOXスピーカー情報を取得し、整形
    speaker_map = get_voicevox_speakers()
    if not speaker_map:
        return

    # 音声設定プロファイルを読み込む
    voice_configs = load_voice_config()
    if not voice_configs:
        return

    # 台本ファイルを選択させる
    available_scripts = get_available_scripts()
    selected_script_name = select_script_file(available_scripts)
    if not selected_script_name:
        return
    script_path = os.path.join(SCRIPT_DIR, selected_script_name)

    # 音声設定プロファイルを選択させる
    selected_profile_name = select_voice_profile(voice_configs)
    if not selected_profile_name:
        return
    selected_profile = voice_configs[selected_profile_name]

    # 選択された台本ファイルを読み込む
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_text = f.read()
    except Exception as e:
        print(f"エラー: 台本ファイルの読み込みに失敗しました: {e}")
        return

    # スピーカーIDを決定
    speaker_name = selected_profile.get("speaker_name")
    style_name = selected_profile.get("style_name")

    if not speaker_name or not style_name:
        print("エラー: 設定プロファイルに 'speaker_name' または 'style_name' が指定されていません。")
        return

    if speaker_name not in speaker_map:
        print(f"エラー: 指定されたスピーカー名 '{speaker_name}' はVOICEVOXエンジンに存在しません。")
        print("利用可能なスピーカー名:", ", ".join(speaker_map.keys()))
        return

    if style_name not in speaker_map[speaker_name]:
        print(f"エラー: 指定されたスタイル名 '{style_name}' はスピーカー '{speaker_name}' に存在しません。")
        print(f"利用可能なスタイル名 ({speaker_name}):", ", ".join(speaker_map[speaker_name].keys()))
        return

    voicevox_speaker_id = speaker_map[speaker_name][style_name]

    print(f"選択されたスピーカー: {speaker_name} ({style_name}), ID: {voicevox_speaker_id}")

    # 音声合成クエリを生成
    audio_query = generate_audio_query(
        script_text,
        voicevox_speaker_id,
        selected_profile.get("speed", 1.0),
        selected_profile.get("pitch", 0.0)
    )
    if not audio_query:
        return

    # 音声を合成
    audio_content = synthesize_voice(voicevox_speaker_id, audio_query)
    if not audio_content:
        return

    # 音声ファイルを保存
    # 生成する音声のテーマを入力させる
    theme = input("生成する音声のテーマを入力してください (例: 自己紹介、挨拶など): ")
    if not theme:
        print("テーマが入力されませんでした。処理を中断します。")
        return

    # ファイル名に使えるようにテーマをサニタイズ
    # 空白、特殊文字などをアンダースコアに置換し、ファイル名として安全な形式にする
    sanitized_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '_', '-')).strip()
    sanitized_theme = sanitized_theme.replace(' ', '_').replace('-', '_')
    if not sanitized_theme:
        sanitized_theme = "untitled" # サニタイズ後も空になった場合

    # 日付を取得 (YYYY-MM-dd)
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")

    output_filename = f"{today_date}_{sanitized_theme}.wav"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    try:
        with open(output_path, 'wb') as f:
            f.write(audio_content)
        print(f"\n✅ 音声が正常に生成され、'{output_path}' に保存されました。")
    except Exception as e:
        print(f"エラー: 音声ファイルの保存に失敗しました: {e}")

if __name__ == "__main__":
    main()
