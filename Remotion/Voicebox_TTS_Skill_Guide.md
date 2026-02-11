# Voicebox自動音声生成スキル 利用ガイド

## はじめに

このガイドでは、VOICEVOXエンジンとPythonスクリプトを使用して、台本から音声を自動生成するスキル (`generate_voice.py`) の利用方法を説明します。このスキルを使うことで、指定した台本の内容を、選択したVOICEVOXのキャラクターとスタイルで音声ファイルとして出力できます。

## 前提条件

このスキルを利用する前に、以下の準備が必要です。

1.  **Python 3.x のインストール**:
    *   Pythonがインストールされていることを確認してください。
    *   必要なライブラリ `requests` をインストールしてください。
        ```bash
        # uv がインストールされている場合（推奨）
        uv pip install requests
        # pip を使用する場合
        pip install requests
        ```
2.  **VOICEVOXエンジンのインストールと起動**:
    *   VOICEVOX公式サイト ([https://voicevox.hiroshiba.jp/](https://voicevox.hiroshiba.jp/)) から、お使いのOSに合ったVOICEVOXアプリケーションをダウンロードし、インストールしてください。
    *   VOICEVOXアプリケーションを起動し、バックグラウンドでVOICEVOXエンジンが動作している状態にしてください。

### VOICEVOXエンジンのAPIポート確認方法

VOICEVOXエンジンが起動していることを確認し、APIがリッスンしているポート番号（通常は `http://127.0.0.1:50021`）を確認します。

*   **Webブラウザでの確認**: `http://127.0.0.1:50021/docs` にアクセスし、APIドキュメントが表示されれば正常に動作しています。

## プロジェクトのフォルダ構造

スキル関連のファイルは、`Remotion` フォルダ内に以下のように配置されています。

```
Remotion/
├── generate_voice.py         # 音声生成スクリプト本体
├── configs/
│   └── voice_config.json     # 音声設定プロファイル
├── scripts/
│   └── voice_scripts/        # 台本ファイル (.txt または .md) を格納
└── output/
    └── audio/                # 生成された音声ファイル (.wav) の出力先
```

## 台本ファイルの準備

台本はテキストファイルとして用意します。

*   **場所**: `Remotion/scripts/voice_scripts/` フォルダ内に配置してください。
*   **形式**: ファイル拡張子は `.txt` または `.md` にしてください。
*   **内容**: 音声に変換したいテキストを記述します。

**例 (`Remotion/scripts/voice_scripts/sample.txt`):**
```
こんにちは、VOICEVOX自動音声生成スキルへようこそ！
このスキルを使えば、あなたの台本が簡単に音声になります。
```

## 音声設定ファイルの準備 (`voice_config.json`)

`Remotion/configs/voice_config.json` ファイルには、音声生成の各種設定（話者、スタイル、話速など）をプロファイルとして定義します。
このスクリプトは `POST /audio_query` または `POST /audio_query_from_preset` でクエリを作成し、必要に応じて設定値で上書きしてから `POST /synthesis` へ渡します。

*   **場所**: `Remotion/configs/voice_config.json`
*   **構造**: 各プロファイルは以下のキーを持ちます。
    *   `preset_id` (任意): VOICEVOXのプリセットID。指定時は `/audio_query_from_preset` を使用します。
    *   `speaker_name`: VOICEVOXのキャラクター名（例: "ずんだもん", "四国めたん"）
    *   `style_name`: キャラクターのスタイル名（例: "ノーマル", "ささやき", "セクシー"）
    *   `speed`: 話速 (1.0が標準)
    *   `pitch`: ピッチ（音高）(0.0が標準)
    *   `volume`: 音量 (1.0が標準)
    *   `pause_length_scale` (任意): 句読点などの「間」の長さ倍率 (`pauseLengthScale`)
    *   `post_phoneme_length` (任意): 発話終了後の無音秒数 (`postPhonemeLength`)
    *   `pre_phoneme_length` (任意): 発話開始前の無音秒数 (`prePhonemeLength`)
    *   `pause_length` (任意): ポーズ長 (`pauseLength`) ※エンジンが対応している場合のみ有効
    *   `language`: 言語 (現時点では "ja-JP" を推奨)

**例 (`Remotion/configs/voice_config.json`):**
```json
{
  "default": {
    "speaker_name": "ずんだもん",
    "style_name": "ノーマル",
    "speed": 1.0,
    "pitch": 0.0,
    "volume": 1.0,
    "pause_length_scale": 1.0,
    "post_phoneme_length": 0.1,
    "language": "ja-JP"
  },
  "shikoku_metan_whisper": {
    "speaker_name": "四国めたん",
    "style_name": "ささやき",
    "speed": 1.05,
    "pitch": 0.0,
    "volume": 0.9,
    "pause_length_scale": 1.2,
    "post_phoneme_length": 0.25,
    "language": "ja-JP"
  },
  "zundamon_normal": {
    "speaker_name": "ずんだもん",
    "style_name": "ノーマル",
    "speed": 1.0,
    "pitch": 0.0,
    "volume": 1.0,
    "pause_length_scale": 1.0,
    "post_phoneme_length": 0.1,
    "language": "ja-JP"
  }
}
```

### `audio_query_from_preset` 利用時の挙動

- `preset_id` を指定したプロファイルは、まずプリセット値を使って `audio_query_from_preset` でクエリを生成します。
- その後、`speed` / `pitch` / `volume` / `pause_length_scale` / `post_phoneme_length` など、`voice_config.json` に指定した値で最終上書きします。
- 利用中エンジンの `AudioQuery` に存在しないキーは安全にスキップされ、警告メッセージを表示します。

### 新しいプロファイルの追加方法

`voice_config.json` を直接編集し、新しいプロファイル名と設定を追加してください。

**VOICEVOXのキャラクター名とスタイル名の確認方法:**
VOICEVOXアプリケーションを起動し、キャラクター選択画面や、`http://127.0.0.1:50021/docs` の `/speakers` エンドポイントで確認できます。`get_voicevox_speakers()`関数が返す `speaker_map` のキーも参考にしてください。

## 音声生成スクリプトの実行 (`generate_voice.py`)

Zsh環境のターミナルで、プロジェクトのルートディレクトリに移動し、以下のコマンドを実行します。

```bash
python Remotion/generate_voice.py
```

実行後、スクリプトは対話形式で以下の情報を求めます。

1.  **利用可能な台本ファイルの一覧**が表示されるので、使用したい台本の番号を入力します。
2.  **利用可能な音声設定プロファイルの一覧**(`voice_config.json`に定義されているプロファイル名)が表示されるので、使用したい設定の番号を入力します。
3.  **生成する音声の「テーマ」**を入力します。（例: 「自己紹介」「挨拶」など）

## 生成される音声ファイル

*   **出力先**: `Remotion/output/audio/` フォルダに保存されます。
*   **命名規則**: `YYYY-MM-dd_テーマ.wav` の形式でファイルが保存されます。（例: `2024-02-10_自己紹介.wav`）

## トラブルシューティング

*   **`requests` ライブラリがない**:
    *   エラーメッセージ: `ModuleNotFoundError: No module named 'requests'`
    *   解決策: 前提条件のセクションを参照し、`requests`ライブラリをインストールしてください。
*   **VOICEVOXエンジンに接続できない**:
    *   エラーメッセージ: `エラー: VOICEVOXエンジンに接続できませんでした。'http://127.0.0.1:50021' が起動しているか確認してください。`
    *   解決策: VOICEVOXアプリケーションが起動しており、エンジンが動作していることを確認してください。ポート番号が異なる場合は、スクリプトの `VOICEVOX_API_BASE_URL` を修正してください。
*   **指定したスピーカー名やスタイルが見つからない**:
    *   エラーメッセージ: `エラー: 指定されたスピーカー名 '〇〇' はVOICEVOXエンジンに存在しません。` など
    *   解決策: `voice_config.json` に記述されている `speaker_name` や `style_name` が、VOICEVOXアプリケーションで利用可能なものと完全に一致しているか確認してください。

## フィードバックと改善

このスキルは、あなたのフィードバックに基づいて継続的に改善されます。
スクリプトの使用感、生成される音声の品質、エラーメッセージの分かりやすさ、追加してほしい機能など、どんなことでもお気軽にお知らせください。

## 運用ルール（フロー変更時）

音声化フローの質問順、選択肢、入力項目、実行手順を変更した場合は、以下を必ず同時更新してください。

1. `Remotion/generate_voice.py`
2. `.agent/skills/voice-script-launcher/SKILL.md`
3. `Remotion/Voicebox_TTS_Skill_Guide.md`（本書）
