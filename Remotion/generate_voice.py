import requests
import json
import os
import glob
import wave
import io
import re
import shutil
import sys
from typing import Dict, Any, List, Optional, Tuple
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 一文の最大文字数（これを超える場合は読点で分割する）
MAX_SENTENCE_LENGTH = 80

# 並列音声生成のワーカー数
MAX_WORKERS = 4

# VOICEVOXエンジンのAPIエンドポイント
VOICEVOX_API_BASE_URL = "http://127.0.0.1:50021"

# フォルダパス (チームインフォのルートからの相対パス)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Remotionディレクトリ
SCRIPT_DIR = os.path.join(BASE_DIR, "scripts", "voice_scripts")
CONFIG_FILE = os.path.join(BASE_DIR, "configs", "voice_config.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "audio")
TMP_DIR = os.path.join(OUTPUT_DIR, "_tmp_chunks")

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


def generate_chunk_audio(
    chunk_index: int,
    chunk_text: str,
    speaker_id: int,
    speed: float,
    pitch: float,
    volume: float,
    pause_length_scale: Optional[float],
    post_phoneme_length: Optional[float],
    pre_phoneme_length: Optional[float],
    pause_length: Optional[float],
    preset_id: Optional[int],
) -> Tuple[int, bytes]:
    """1チャンクの音声クエリ生成+合成を行い、(index, wav_bytes) を返す。"""
    audio_query = generate_audio_query(
        chunk_text, speaker_id, speed, pitch, volume,
        pause_length_scale, post_phoneme_length, pre_phoneme_length,
        pause_length, preset_id,
    )
    if not audio_query:
        return (chunk_index, b"")
    audio_content = synthesize_voice(speaker_id, audio_query)
    return (chunk_index, audio_content)


def cleanup_tmp_dir():
    """過去の実行で残った _tmp_chunks を削除する"""
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR, ignore_errors=True)
        print(f"  → 前回の一時フォルダを削除しました: {TMP_DIR}")

def split_script_to_chunks(script_text: str) -> List[str]:
    """台本テキストを一文ごとに分割する。長い文は読点でさらに分割する。"""
    # まず「。」で一文ずつに分割（区切り文字を残す）
    sentences = re.split(r'(?<=。)', script_text)
    chunks: List[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= MAX_SENTENCE_LENGTH:
            chunks.append(sentence)
        else:
            # 長い文は読点「、」で分割
            parts = re.split(r'(?<=、)', sentence)
            current = ""
            for part in parts:
                if current and len(current) + len(part) > MAX_SENTENCE_LENGTH:
                    chunks.append(current.strip())
                    current = part
                else:
                    current += part
            if current.strip():
                chunks.append(current.strip())
    return chunks


def print_progress(current: int, total: int, label: str = "進捗"):
    """進捗をパーセンテージとプログレスバーで表示する"""
    percent = current / total * 100 if total > 0 else 0
    bar_length = 30
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    sys.stdout.write(f"\r  {label}: [{bar}] {percent:5.1f}% ({current}/{total})")
    sys.stdout.flush()
    if current == total:
        print()  # 完了時に改行


def main():
    print("VOICEVOX自動音声生成スキルを開始します。")

    # 過去の実行で残った一時ファイルがあれば削除
    cleanup_tmp_dir()

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

    # 音声設定プロファイルを選択させる（presets_mapは後でも再利用する）
    style_id_to_name_map = get_style_id_to_name_map()
    presets_map = get_voicevox_presets()
    selected_profile_name = select_voice_profile(
        voice_configs,
        style_id_to_name_map=style_id_to_name_map,
        presets_map=presets_map,
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

    # スピーカーIDを決定（preset_id があれば優先、presets_mapを再利用）
    preset_id = selected_profile.get("preset_id")
    if preset_id is not None:
        if not presets_map:
            return
        if preset_id not in presets_map:
            print(f"エラー: 指定された preset_id '{preset_id}' はVOICEVOXエンジンに存在しません。")
            print("利用可能な preset_id:", ", ".join(str(k) for k in presets_map.keys()))
            return
        voicevox_speaker_id = presets_map[preset_id]["style_id"]
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

    # ===== Step 1/3: テキスト分割 =====
    print("\n[Step 1/3] 台本テキストを一文ごとに分割しています...")
    chunks = split_script_to_chunks(script_text)
    if not chunks:
        print("エラー: 台本テキストが空です。")
        return
    total_chunks = len(chunks)
    print(f"  → {total_chunks} 個のチャンクに分割しました。")

    # ===== Step 2/3: 各チャンクの音声を並列生成（メモリ内） =====
    print(f"\n[Step 2/3] 各チャンクの音声を並列生成しています (ワーカー数: {MAX_WORKERS})...")
    profile_speed = selected_profile.get("speed", 1.0)
    profile_pitch = selected_profile.get("pitch", 0.0)
    profile_volume = selected_profile.get("volume", 1.0)
    profile_pause_length_scale = selected_profile.get("pause_length_scale")
    profile_post_phoneme_length = selected_profile.get("post_phoneme_length")
    profile_pre_phoneme_length = selected_profile.get("pre_phoneme_length")
    profile_pause_length = selected_profile.get("pause_length")
    effective_preset_id = preset_id if preset_id is not None else None

    # 結果を格納する辞書 (index -> wav_bytes)、スレッドセーフにカウンタを管理
    import threading
    audio_results: Dict[int, bytes] = {}
    error_count = 0
    completed = 0
    progress_lock = threading.Lock()

    def on_chunk_done(future):
        nonlocal completed, error_count
        chunk_idx, wav_data = future.result()
        with progress_lock:
            completed += 1
            if wav_data:
                audio_results[chunk_idx] = wav_data
            else:
                error_count += 1
            print_progress(completed, total_chunks, "音声生成")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, chunk in enumerate(chunks):
            future = executor.submit(
                generate_chunk_audio,
                i, chunk, voicevox_speaker_id,
                profile_speed, profile_pitch, profile_volume,
                profile_pause_length_scale, profile_post_phoneme_length,
                profile_pre_phoneme_length, profile_pause_length,
                effective_preset_id,
            )
            future.add_done_callback(on_chunk_done)
            futures.append(future)
        # 全タスクの完了を待つ
        for f in futures:
            f.result()

    if not audio_results:
        print("\nエラー: 音声を1つも生成できませんでした。")
        return

    if error_count > 0:
        print(f"  ({error_count} 個のチャンクでエラーが発生しました)")

    # ===== Step 3/3: メモリ内でWAVを結合して出力 =====
    theme = input("生成する音声のテーマを入力してください (例: 自己紹介、挨拶など): ")
    if not theme:
        print("テーマが入力されませんでした。処理を中断します。")
        return

    sanitized_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '_', '-')).strip()
    sanitized_theme = sanitized_theme.replace(' ', '_').replace('-', '_')
    if not sanitized_theme:
        sanitized_theme = "untitled"

    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{today_date}_{sanitized_theme}.wav"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # チャンク番号順にソートして結合
    sorted_indices = sorted(audio_results.keys())
    success_count = len(sorted_indices)

    print(f"\n[Step 3/3] {success_count} 個の音声データを結合しています...")

    try:
        first_wav_io = io.BytesIO(audio_results[sorted_indices[0]])
        with wave.open(first_wav_io, 'rb') as first_wav:
            params = first_wav.getparams()

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with wave.open(output_path, 'wb') as out_wav:
            out_wav.setparams(params)
            for j, idx in enumerate(sorted_indices):
                print_progress(j, success_count, "結合中 ")
                wav_io = io.BytesIO(audio_results[idx])
                with wave.open(wav_io, 'rb') as seg_wav:
                    out_wav.writeframes(seg_wav.readframes(seg_wav.getnframes()))
            print_progress(success_count, success_count, "結合中 ")
    except Exception as e:
        print(f"\nエラー: 音声ファイルの結合に失敗しました: {e}")
        return

    print(f"\n完了! 音声ファイルが '{output_path}' に保存されました。")
    print(f"   チャンク数: {success_count} / エラー: {error_count}")

if __name__ == "__main__":
    main()
