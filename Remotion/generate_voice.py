import requests
import json
import os
import glob
import wave
import io
from typing import Dict, Any, List, Optional
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
        return {}
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

def select_voice_profile(
    voice_configs: Dict[str, Any],
    style_id_to_name_map: Optional[Dict[int, Dict[str, str]]] = None,
    presets_map: Optional[Dict[int, Dict[str, Any]]] = None,
) -> str:
    """ユーザーに音声設定プロファイルを選択させる"""
    if not voice_configs:
        print("エラー: 音声設定プロファイルがありません。")
        return ""

    print("\n--- 利用可能な音声設定プロファイル ---")
    profile_names = list(voice_configs.keys())
    profile_labels = []
    for profile_name in profile_names:
        profile = voice_configs.get(profile_name, {})
        speaker_name = profile.get("speaker_name")
        style_name = profile.get("style_name")
        preset_id = profile.get("preset_id")

        if speaker_name and style_name:
            display_label = f"【{style_name}】{speaker_name}"
        elif preset_id is not None:
            display_label = f"preset_id={preset_id}"
            if presets_map and style_id_to_name_map:
                preset = presets_map.get(preset_id)
                if preset:
                    style_id = preset.get("style_id")
                    if style_id in style_id_to_name_map:
                        style_info = style_id_to_name_map[style_id]
                        display_label = f"【{style_info['style_name']}】{style_info['speaker_name']}"
        else:
            display_label = profile_name

        profile_labels.append(display_label)

    for i in range(len(profile_names)):
        print(f"{i+1}: {profile_labels[i]}")

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

def get_style_id_to_name_map() -> Dict[int, Dict[str, str]]:
    """style_id から speaker_name/style_name を引ける辞書を作る"""
    try:
        response = requests.get(f"{VOICEVOX_API_BASE_URL}/speakers")
        response.raise_for_status()
        raw_speakers_data = response.json()
        style_map: Dict[int, Dict[str, str]] = {}
        for speaker_data in raw_speakers_data:
            speaker_name = speaker_data["name"]
            for style in speaker_data["styles"]:
                style_map[style["id"]] = {
                    "speaker_name": speaker_name,
                    "style_name": style["name"],
                }
        return style_map
    except requests.exceptions.RequestException:
        return {}

def get_voicevox_presets() -> Dict[int, Dict[str, Any]]:
    """VOICEVOXエンジンからプリセット一覧を取得する"""
    try:
        response = requests.get(f"{VOICEVOX_API_BASE_URL}/presets")
        response.raise_for_status()
        presets = response.json()
        return {preset["id"]: preset for preset in presets}
    except requests.exceptions.RequestException as e:
        print(f"VOICEVOXプリセット情報の取得中にエラーが発生しました: {e}")
        return {}

def generate_audio_query(
    text: str,
    speaker_id: int,
    speed: float = 1.0,
    pitch: float = 0.0,
    volume: float = 1.0,
    pause_length_scale: Optional[float] = None,
    post_phoneme_length: Optional[float] = None,
    pre_phoneme_length: Optional[float] = None,
    pause_length: Optional[float] = None,
    preset_id: Optional[int] = None,
) -> Dict[str, Any]:
    """音声合成クエリを生成する"""
    if preset_id is not None:
        endpoint = "/audio_query_from_preset"
        params = {
            "text": text,
            "preset_id": preset_id,
        }
    else:
        endpoint = "/audio_query"
        params = {
            "text": text,
            "speaker": speaker_id,
        }

    try:
        response = requests.post(f"{VOICEVOX_API_BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        query = response.json()
        
        # 設定ファイル側の値で最終上書き（共通パラメータ）
        query["speedScale"] = speed
        query["pitchScale"] = pitch
        query["volumeScale"] = volume

        # 追加の任意パラメータ（エンジン差異を考慮し、存在するキーのみ上書き）
        optional_overrides = {
            "pauseLengthScale": pause_length_scale,
            "postPhonemeLength": post_phoneme_length,
            "prePhonemeLength": pre_phoneme_length,
            "pauseLength": pause_length,
        }
        for query_key, value in optional_overrides.items():
            if value is None:
                continue
            if query_key in query:
                query[query_key] = value
            else:
                print(
                    f"警告: このVOICEVOXエンジンのAudioQueryに '{query_key}' がないため、"
                    "設定値をスキップしました。"
                )
        return query
    except requests.exceptions.RequestException as e:
        print(f"音声クエリの生成中にエラーが発生しました: {e}")
        return {}

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
    style_id_to_name_map = get_style_id_to_name_map()
    presets_map_for_label = get_voicevox_presets()
    selected_profile_name = select_voice_profile(
        voice_configs,
        style_id_to_name_map=style_id_to_name_map,
        presets_map=presets_map_for_label,
    )
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

    # スピーカーIDを決定（preset_id があれば優先）
    preset_id = selected_profile.get("preset_id")
    if preset_id is not None:
        presets = get_voicevox_presets()
        if not presets:
            return
        if preset_id not in presets:
            print(f"エラー: 指定された preset_id '{preset_id}' はVOICEVOXエンジンに存在しません。")
            print("利用可能な preset_id:", ", ".join(str(k) for k in presets.keys()))
            return
        voicevox_speaker_id = presets[preset_id]["style_id"]
        print(f"選択されたプリセットID: {preset_id}, スタイルID: {voicevox_speaker_id}")
    else:
        speaker_map = get_voicevox_speakers()
        if not speaker_map:
            return

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

    # テキストを段落ごとに分割（空行区切り）
    chunks = [chunk.strip() for chunk in script_text.split("\n\n") if chunk.strip()]
    if not chunks:
        print("エラー: 台本テキストが空です。")
        return

    print(f"\n台本を {len(chunks)} 個の段落に分割して音声生成します。")

    # 共通パラメータ
    profile_speed = selected_profile.get("speed", 1.0)
    profile_pitch = selected_profile.get("pitch", 0.0)
    profile_volume = selected_profile.get("volume", 1.0)
    profile_pause_length_scale = selected_profile.get("pause_length_scale")
    profile_post_phoneme_length = selected_profile.get("post_phoneme_length")
    profile_pre_phoneme_length = selected_profile.get("pre_phoneme_length")
    profile_pause_length = selected_profile.get("pause_length")
    effective_preset_id = preset_id if preset_id is not None else None

    # 各段落ごとに音声合成
    audio_segments: List[bytes] = []
    for i, chunk in enumerate(chunks):
        print(f"  [{i+1}/{len(chunks)}] 音声生成中...")
        audio_query = generate_audio_query(
            chunk,
            voicevox_speaker_id,
            profile_speed,
            profile_pitch,
            profile_volume,
            profile_pause_length_scale,
            profile_post_phoneme_length,
            profile_pre_phoneme_length,
            profile_pause_length,
            effective_preset_id,
        )
        if not audio_query:
            print(f"  エラー: 段落 {i+1} の音声クエリ生成に失敗しました。スキップします。")
            continue

        audio_content = synthesize_voice(voicevox_speaker_id, audio_query)
        if not audio_content:
            print(f"  エラー: 段落 {i+1} の音声合成に失敗しました。スキップします。")
            continue

        audio_segments.append(audio_content)

    if not audio_segments:
        print("エラー: 音声を1つも生成できませんでした。")
        return

    print(f"\n{len(audio_segments)} 個の音声セグメントを結合しています...")

    # WAVファイルを結合
    combined_audio = io.BytesIO()
    with wave.open(io.BytesIO(audio_segments[0]), 'rb') as first_wav:
        params = first_wav.getparams()

    with wave.open(combined_audio, 'wb') as out_wav:
        out_wav.setparams(params)
        for segment in audio_segments:
            with wave.open(io.BytesIO(segment), 'rb') as seg_wav:
                out_wav.writeframes(seg_wav.readframes(seg_wav.getnframes()))

    # 音声ファイルを保存
    # 生成する音声のテーマを入力させる
    theme = input("生成する音声のテーマを入力してください (例: 自己紹介、挨拶など): ")
    if not theme:
        print("テーマが入力されませんでした。処理を中断します。")
        return

    # ファイル名に使えるようにテーマをサニタイズ
    sanitized_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '_', '-')).strip()
    sanitized_theme = sanitized_theme.replace(' ', '_').replace('-', '_')
    if not sanitized_theme:
        sanitized_theme = "untitled"

    # 日付を取得 (YYYY-MM-dd)
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")

    output_filename = f"{today_date}_{sanitized_theme}.wav"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(combined_audio.getvalue())
        print(f"\n✅ 音声が正常に生成され、'{output_path}' に保存されました。")
    except Exception as e:
        print(f"エラー: 音声ファイルの保存に失敗しました: {e}")

if __name__ == "__main__":
    main()
