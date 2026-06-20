# macos-arm64 (Apple Silicon) artifacts

まだビルド済みバイナリがありません。**Apple Silicon Mac で初めて `setup` を実行した人**が
`setup/headroom/install.sh` 経由でビルドし、ここに wheel が生成されます（要 Rust／初回のみ数分）。

生成された `headroom_ai-*.whl` をコミット（`git add` → push）すると、
次の Apple Silicon メンバーは**ビルド不要の高速インストール**になります。

> Apple Silicon は `ort` の公式 arm64 バイナリを使う通常ビルドのため、Intel のような
> パッチや外部 ONNX dylib は不要（wheel が自己完結）。
