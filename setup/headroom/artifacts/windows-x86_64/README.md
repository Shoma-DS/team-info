# windows-x86_64 artifacts

まだビルド済みバイナリがありません。**Windows で初めて `setup` を実行した人**が
`setup/headroom/install.ps1` 経由でビルドし、ここに wheel（と `onnxruntime.dll`）が生成されます。

生成物をコミットすると、次の Windows メンバーはビルド不要になります。

> Windows は Cargo 設定が既に `ort-load-dynamic` のため、ビルドに Rust + MSVC build tools、
> 実行時に `onnxruntime.dll` が必要（このフォルダに同梱する想定）。**未検証**のため初回は要確認。
