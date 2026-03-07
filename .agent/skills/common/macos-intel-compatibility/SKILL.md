---
name: macos-intel-compatibility
description: Intel Mac (x86_64) での Python/PyTorch プロジェクトの互換性問題を解決するためのスキル。GPU がない環境での対処法、依存関係の調整、パッチの適用方法を含む。
---

# macOS Intel 互換性スキル

## 環境情報
- **OS**: macOS（Intel x86_64）
- **Python**: 3.11（uv 経由でインストール）
- **パッケージマネージャ**: uv（PATH上の `uv` を使う。見つからない場合は `python -m uv` でもよい）
- **GPU**: なし（CPU のみ）

## よくある問題と解決策

### 1. `torch.xpu` が見つからない
PyTorch の CPU ビルドには XPU サポートがないため、`diffusers` などが `torch.xpu` にアクセスしようとするとエラーになる。

**解決策**: `MockXPU` クラスでパッチを当てる（`acestep/__init__.py` に実装済み）

### 2. `torch.distributed.device_mesh` が見つからない
PyTorch 2.2.x には `device_mesh` モジュールがない。

**解決策**: `MockDeviceMesh` クラスでパッチを当てる（`acestep/__init__.py` に実装済み）

### 3. NumPy 2.x との互換性
PyTorch 2.2.x は NumPy 2.x と互換性がない。

**解決策**: `pyproject.toml` で `numpy<2` を指定

### 4. `numba` / `llvmlite` のビルド失敗
Intel Mac では `llvmlite` のビルドに `llvm-config` が必要だが、通常インストールされていない。

**解決策**: `numba` を依存関係から除外し、JIT デコレータをコメントアウト

### 5. `torchao` の互換性
`torchao` は PyTorch 2.2.x と互換性がない。

**解決策**: `torchao` を依存関係から除外

## uv コマンド

```bash
# 依存関係の同期
uv sync

# スクリプトの実行
uv run <script.py>
```
