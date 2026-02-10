#!/bin/bash

# .venvディレクトリを作成し、仮想環境をセットアップ
python3 -m venv .venv

# 仮想環境をアクティブ化
source .venv/bin/activate

# 必要なPythonパッケージをインストール
pip install requests

echo "仮想環境のセットアップと依存ライブラリのインストールが完了しました。"
echo "スクリプトを実行するには 'source .venv/bin/activate' で仮想環境をアクティブにしてから 'python generate_voice.py' を実行してください。"
echo "または './run.sh' を実行してください。"