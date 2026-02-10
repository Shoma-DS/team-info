---
name: ace-step-music-generation
description: ACE-Step 1.5 を使って音楽を生成するためのスキル。音楽生成、モデルのセットアップ、Gradio UIの起動、generate_sample.pyの実行に関する質問があるときに使用します。Intel Mac での互換性パッチも含みます。
---

# ACE-Step 1.5 音楽生成スキル

## 概要
ACE-Step 1.5 は AI による音楽生成モデルです。テキストの説明と歌詞から音楽を生成できます。

## プロジェクトの場所
`/Users/deguchishouma/team-info/ACE-Step-1.5`

## 起動方法

### Web UI（Gradio）を起動する
```bash
cd /Users/deguchishouma/team-info/ACE-Step-1.5
bash start_gradio_ui_macos.sh
```
- UI 言語は `start_gradio_ui_macos.sh` 内の `LANGUAGE` 変数で設定（`ja` が設定済み）
- ブラウザで `http://127.0.0.1:7860` を開く

### スクリプトで音楽生成
```bash
cd /Users/deguchishouma/team-info/ACE-Step-1.5
uv run generate_sample.py
```

## Intel Mac での注意点
- GPU がないため CPU のみで動作（非常に遅い）
- `torch.xpu` と `torch.distributed.device_mesh` のパッチが `acestep/__init__.py` に適用済み
- `numba` と `torchao` は互換性の問題で無効化済み
- `numpy<2` に制限済み（PyTorch 2.2.2 との互換性のため）

## 推奨環境
- Google Colab（NVIDIA GPU 付き）での実行を推奨
- Apple Silicon Mac（M1〜M4）では MLX バックエンドで動作可能

## 主要ファイル
- `generate_sample.py` - サンプル音楽生成スクリプト
- `monitor_download.py` - モデルダウンロード進捗確認ツール
- `start_gradio_ui_macos.sh` - macOS 用 Gradio UI 起動スクリプト
- `acestep/__init__.py` - Intel Mac 互換性パッチ
- `pyproject.toml` - 依存関係設定
