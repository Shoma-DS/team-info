# Headroom — トークン圧縮プロキシ（team-info 同梱）

`claude` / `codex` が AI に送る前のやりとりを、ローカルの常駐プロキシ（`http://127.0.0.1:8787`）が
通り道で圧縮・キャッシュ整列する仕組みです。`setup_mac.sh` / `setup_windows.ps1` から
**機種を自動判別**して入ります。

> 例えるなら「AI とのあいだに通訳さんを 1 人はさんで、長い言葉を短くしてから渡す」イメージ。
> 通訳さん（プロキシ）は PC 起動中ずっと裏で待機します。

---

## ⚠️ 正直な注記（先に読んでください）

- **実機検証できたのは Intel Mac のみ**です。Apple Silicon / Windows / Linux の分岐は
  ドキュメントと挙動からの設計で、**各機種で初回 1 回流して微修正が要る**見込みです。
  初回実行した人はログを共有してください（このフォルダの該当 `artifacts/<platform>/README.md` 参照）。
- **圧縮の実節約効果は未実証**です。単発の短いテストでは削減 0%、キャッシュ整列のみ観測でした。
  長い作業ほど効きやすい設計ですが、効果は実使用で `check.sh` を見ながら判断してください。
- プロキシが落ちると `claude` / `codex` が一時的に通らなくなります（mac は launchd の KeepAlive で自動復帰）。
  困ったら下の「ロールバック」で即元に戻せます。

---

## 入る仕組み（機種マトリクス）

| 機種 | wheel ビルド | ONNX ランタイム | 検証 |
|---|---|---|---|
| macOS x86_64 (Intel) | **要 1 行パッチ** `ort-download-binaries-rustls-tls` → `ort-load-dynamic` | 外部 `libonnxruntime.dylib` 同梱必須 | ✅ 検証済み・成果物同梱 |
| macOS arm64 (Apple Silicon) | 通常ビルド（`ort` 公式 arm64 バイナリ） | wheel 自己完結・不要 | ⚠️ 未検証（要 Rust） |
| Windows x86_64 | 通常ビルド（Cargo は既に win=load-dynamic） | 外部 `onnxruntime.dll` 必須 | ⚠️ 未検証（要 Rust + MSVC build tools） |
| Linux x86_64 | 通常ビルド | wheel 自己完結・不要 | ⚠️ おまけ・未検証（要 Rust） |

- ビルド済み wheel は `cp310-abi3` ＝ **Python 3.10 以上で共通**（team の pyenv 3.11.9 でも可）。
- 配布方式は**ハイブリッド**：`artifacts/<platform>/` にビルド済みがあれば高速インストール、
  無ければその場でビルドして同フォルダにキャッシュ（コミットすれば次の人はビルド不要）。
- `artifacts/**` のバイナリ（`*.whl *.dylib *.dll *.so *.tar.gz *.zip`）は **git-lfs** 管理です。

### なぜ Intel Mac だけパッチが要るのか
headroom の Rust 拡張は `fastembed` + `magika` 経由で `ort`（ONNX Runtime）に依存しますが、
`ort` は **`x86_64-apple-darwin`（Intel Mac）用の prebuilt バイナリを配布していません**。
そこで Cargo の feature を `ort-load-dynamic` に変え、ONNX 本体は実行時に外部 dylib
（`~/.headroom/lib/libonnxruntime.dylib`、`ORT_DYLIB_PATH` で指定）から読み込ませています。

---

## ファイル構成

```
setup/headroom/
├── README.md            このファイル
├── install.sh           macOS / Linux インストーラ（機種自動判別）
├── install.ps1          Windows インストーラ（未検証）
├── check.sh             節約レポート（macOS / Linux・小学生向け表示）
├── check.ps1            節約レポート（Windows）
├── .gitattributes       artifacts のバイナリを git-lfs 指定
└── artifacts/
    ├── macos-x86_64/    ✅ wheel + libonnxruntime*.dylib + PATCHED-src.tar.gz（Intel・同梱済み）
    ├── macos-arm64/     初回ビルドで生成（README のみ）
    ├── windows-x86_64/  初回ビルドで生成（wheel + onnxruntime.dll）
    └── linux-x86_64/    初回ビルドで生成（README のみ）
```

---

## 使い方

### セットアップ（通常）
`setup_mac.sh` / `setup_windows.ps1` を流せば、headroom ステップで自動的に入ります（非致命：
失敗しても setup 全体は止まりません）。新しいターミナルから `claude` / `codex` がプロキシ経由になります。

### 手動で入れる
```bash
# macOS / Linux
bash setup/headroom/install.sh --python "$(pyenv root)/versions/3.11.9/bin/python3" --repo-root "$PWD"
```
```powershell
# Windows
powershell -ExecutionPolicy Bypass -File setup\headroom\install.ps1 `
    -PythonExe "$env:USERPROFILE\.pyenv\pyenv-win\versions\3.11.9\python.exe" -RepoRoot "$PWD"
```

### どれだけ圧縮できたか見る
```bash
bash setup/headroom/check.sh          # macOS / Linux
```
```powershell
powershell -ExecutionPolicy Bypass -File setup\headroom\check.ps1   # Windows
```
「前回チェックからの今回ぶん」と「ずっとの合計」を日本語で表示します。

---

## 動作確認

```bash
curl -s http://127.0.0.1:8787/readyz    # ready=true, rust_core=loaded なら OK
curl -s http://127.0.0.1:8787/stats     # 圧縮・キャッシュの統計（check.sh が整形）
```

---

## ロールバック（元に戻す）

```bash
# 1) 配線を外す（claude / codex をプロキシ経由から戻す）
headroom mcp uninstall            || true
headroom unwrap codex             || true   # codex のラップ解除
headroom install remove           || true   # 常駐サービス＋claude ルーティング撤去

# 2) PATH 追記ブロックを削除（手で）
#    ~/.zshrc / ~/.zprofile / ~/.bashrc / ~/.profile の
#    「>>> headroom extra (team-info) >>>」～「<<< headroom extra (team-info) <<<」を削除
#    （install apply が入れた headroom 管理ブロックは install remove が消します）

# 3) パッケージと作業ディレクトリを消す
python3 -m pip uninstall -y headroom-ai
rm -rf ~/.headroom
```

Windows:
```powershell
& $HrBin mcp uninstall
& $HrBin unwrap codex
& $HrBin install remove
[System.Environment]::SetEnvironmentVariable("ORT_DYLIB_PATH", $null, "User")
# User PATH から Scripts 追記を手で削除、~/.claude.json / ~/.codex/config.toml の headroom 項目を戻す
& $PythonExe -m pip uninstall -y headroom-ai
Remove-Item -Recurse -Force "$env:USERPROFILE\.headroom"
```

---

## トラブルシュート

| 症状 | 対処 |
|---|---|
| `No module named 'headroom._core'` | wheel が `_core` 無し。`install.sh` を再実行（ビルドし直す）。 |
| `ort does not provide prebuilt binaries for x86_64-apple-darwin` | Intel Mac。パッチ済み src（`artifacts/macos-x86_64/*-PATCHED-src.tar.gz`）が使われているか確認。 |
| プロキシが `/readyz` を返さない | `~/.headroom/deploy/default/` のログ確認。mac は `launchctl kickstart -k gui/$(id -u)/com.headroom.default`。 |
| `ImportError: 'h2' package not installed` | `pip install --user "httpx[http2]" h2` を再実行。 |
| Windows で ONNX エラー | `~/.headroom/lib/onnxruntime.dll` を配置し `ORT_DYLIB_PATH` を確認。 |

---

## 設計上の注意

- 配線・常駐・可逆化は headroom 自身の `install apply` / `init codex` / `mcp install` / `install remove` を利用しています（再実装していません）。
- 実機で判明した必須ワークアラウンドを installer に内包：
  `--providers manual`（`--providers auto` は openclaw のバグで落ちる）、launchd ラッパーへ `ORT_DYLIB_PATH` 注入、
  MCP 起動コマンドの絶対パス化、`httpx[http2] h2 mcp` 依存追加。
- git-lfs に数十 MB のバイナリが入ります（OS × バージョンで増える）。LFS 帯域・容量に注意。
