#!/usr/bin/env bash
# =============================================================================
# Headroom インストーラ (macOS / Linux)
# =============================================================================
# トークン圧縮プロキシ headroom を機種に合わせて入れ、claude / codex を
# 自動でプロキシ経由にする。team-info setup から呼ばれる想定だが単体実行も可。
#
#   bash setup/headroom/install.sh [--python <python3>] [--repo-root <dir>]
#
# 方針:
#   - artifacts/<platform>/ にビルド済み wheel があれば使う（Rust 不要・高速）
#   - 無ければその場でビルドし、artifacts/<platform>/ にキャッシュ（要 Rust）
#   - 失敗しても exit 1 はするが、呼び出し側 setup は `|| warn` で継続する想定（非致命）
#
# 機種別:
#   macOS x86_64(Intel) … 1行パッチ(ort-load-dynamic)＋外部 ONNX dylib が必要【検証済み】
#   macOS arm64         … 通常ビルド(ort 公式arm64)・ONNX不要【未検証】
#   Linux x86_64/arm64  … 通常ビルド・ONNX不要【未検証】
# =============================================================================
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
fail()    { echo -e "${RED}[ERROR]${RESET} $*"; }
step()    { echo -e "\n${BOLD}━━━ $* ━━━${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PYTHON=""
REPO_ROOT="$DEFAULT_REPO_ROOT"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)    PYTHON="${2:-}"; shift 2 ;;
    --repo-root) REPO_ROOT="${2:-}"; shift 2 ;;
    *) warn "未知の引数: $1"; shift ;;
  esac
done

# ── Python を決める（pyenv 3.11 優先 → python3）──────────────────────────────
if [[ -z "$PYTHON" || ! -x "$PYTHON" ]]; then
  if command -v pyenv &>/dev/null; then
    _v="$(pyenv versions --bare 2>/dev/null | grep '^3\.11' | tail -1)"
    [[ -n "$_v" ]] && PYTHON="$(pyenv root)/versions/$_v/bin/python3"
  fi
fi
[[ -x "${PYTHON:-}" ]] || PYTHON="$(command -v python3 || true)"
[[ -x "${PYTHON:-}" ]] || { fail "python3 が見つかりません"; exit 1; }
info "Python: $PYTHON ($($PYTHON --version 2>&1))"

PY_USER_BASE="$($PYTHON -c 'import site; print(site.USER_BASE)')"
PY_BIN_DIR="$PY_USER_BASE/bin"
HRBIN="$PY_BIN_DIR/headroom"
ARTIFACTS="$REPO_ROOT/setup/headroom/artifacts"
HR_HOME="$HOME/.headroom"
ONNX_DIR="$HR_HOME/lib"

# ── 機種判別 ─────────────────────────────────────────────────────────────────
OS="$(uname -s)"; ARCH="$(uname -m)"
NEEDS_ONNX=0   # load-dynamic 機種だけ 1（外部 ONNX を runtime に置く）
case "$OS/$ARCH" in
  Darwin/arm64)         PLATFORM="macos-arm64" ;;
  Darwin/x86_64)        PLATFORM="macos-x86_64"; NEEDS_ONNX=1 ;;
  Linux/x86_64)         PLATFORM="linux-x86_64" ;;
  Linux/aarch64|Linux/arm64) PLATFORM="linux-arm64" ;;
  *) warn "未対応の機種です: $OS/$ARCH — headroom はスキップします"; exit 0 ;;
esac
step "Headroom インストール (platform=$PLATFORM)"

# ── Rust ツールチェーンを用意（ビルドが必要なときだけ）───────────────────────
ensure_rust_on_path() {
  command -v cargo &>/dev/null && return 0
  local tc="$HOME/.rustup/toolchains"
  if [[ -d "$tc" ]]; then
    local cargobin
    cargobin="$(ls -d "$tc"/*/bin 2>/dev/null | head -1)"
    if [[ -x "$cargobin/cargo" ]]; then export PATH="$cargobin:$PATH"; command -v cargo &>/dev/null && return 0; fi
  fi
  [[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"
  command -v cargo &>/dev/null && return 0
  info "Rust ツールチェーンを導入します（rustup, 数分）..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal >/dev/null 2>&1
  [[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"
  command -v cargo &>/dev/null
}

# ── ONNX runtime dylib（macOS Intel）を用意 ─────────────────────────────────
ensure_onnx_macos() {
  mkdir -p "$ONNX_DIR"
  # 1) artifacts に同梱の dylib
  local a
  a="$(ls "$ARTIFACTS/$PLATFORM"/libonnxruntime*.dylib 2>/dev/null | grep -v -- '->' | head -1)"
  if [[ -n "$a" ]]; then cp -f "$a" "$ONNX_DIR/"; fi
  # 2) artifacts に無ければ brew の onnxruntime
  if ! ls "$ONNX_DIR"/libonnxruntime*.dylib &>/dev/null; then
    if command -v brew &>/dev/null; then
      local p; p="$(brew --prefix onnxruntime 2>/dev/null)"
      [[ -d "$p/lib" ]] || { info "onnxruntime を brew で入れます..."; brew install onnxruntime >/dev/null 2>&1; p="$(brew --prefix onnxruntime 2>/dev/null)"; }
      [[ -d "$p/lib" ]] && cp -f "$p"/lib/libonnxruntime*.dylib "$ONNX_DIR/" 2>/dev/null
    fi
  fi
  # symlink を整える
  local real; real="$(ls "$ONNX_DIR"/libonnxruntime.*.dylib 2>/dev/null | grep -E 'libonnxruntime\.[0-9]' | head -1)"
  if [[ -n "$real" ]]; then
    (cd "$ONNX_DIR" && ln -sf "$(basename "$real")" libonnxruntime.dylib)
  fi
  [[ -e "$ONNX_DIR/libonnxruntime.dylib" ]]
}

# ── wheel をビルド ───────────────────────────────────────────────────────────
build_wheel() {
  step "ビルド済み wheel が無いのでソースからビルドします（要 Rust）"
  ensure_rust_on_path || { fail "Rust を用意できませんでした"; return 1; }
  info "cargo: $(command -v cargo)"
  local out="/tmp/hr_wheel_build.$$"; rm -rf "$out"; mkdir -p "$out"
  export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}"

  if [[ "$PLATFORM" == "macos-x86_64" ]]; then
    # Intel mac: パッチ済みソースから（ort-load-dynamic）
    local src
    src="$(ls "$ARTIFACTS/$PLATFORM"/headroom_ai-*-PATCHED-src.tar.gz 2>/dev/null | head -1)"
    if [[ -z "$src" ]]; then
      info "パッチ済みソースが無いので sdist を取得してパッチします..."
      local sd="/tmp/hr_sdist.$$"; rm -rf "$sd"; mkdir -p "$sd"; ( cd "$sd"
        local url; url="$(curl -s https://pypi.org/pypi/headroom-ai/json | "$PYTHON" -c "import sys,json;u=[x['url'] for x in json.load(sys.stdin)['urls'] if x['packagetype']=='sdist'];print(u[0] if u else '')")"
        [[ -n "$url" ]] || { fail "sdist URL を取得できません"; exit 1; }
        curl -sL "$url" -o hr.tar.gz && tar xzf hr.tar.gz )
      local d; d="$(ls -d "$sd"/headroom_ai-* 2>/dev/null | head -1)"
      [[ -n "$d" ]] || { fail "sdist 展開に失敗"; return 1; }
      # 1行パッチ: 非Windows の fastembed を load-dynamic に
      perl -0pi -e 's/ort-download-binaries-rustls-tls/ort-load-dynamic/g' "$d/crates/headroom-core/Cargo.toml"
      src="$d"
    fi
    info "wheel をビルド中（LTO release・数分）..."
    "$PYTHON" -m pip wheel --no-deps -w "$out" "$src" || { fail "wheel ビルド失敗"; return 1; }
  else
    # arm64-mac / linux: 通常ビルド（ort 公式バイナリ）
    info "wheel をビルド中（通常ビルド・数分）..."
    "$PYTHON" -m pip wheel --no-deps -w "$out" headroom-ai || { fail "wheel ビルド失敗"; return 1; }
  fi

  WHEEL="$(ls "$out"/headroom_ai-*.whl 2>/dev/null | head -1)"
  [[ -n "$WHEEL" ]] || { fail "ビルド成果の wheel が見つかりません"; return 1; }
  # キャッシュへ保存（人間が後でコミットすれば次の人は高速）
  mkdir -p "$ARTIFACTS/$PLATFORM"; cp -f "$WHEEL" "$ARTIFACTS/$PLATFORM/"
  success "ビルド完了: $(basename "$WHEEL") → artifacts/$PLATFORM/ にキャッシュ"
}

# ── 1. wheel を入手 ──────────────────────────────────────────────────────────
step "1. headroom wheel を入手"
WHEEL="$(ls "$ARTIFACTS/$PLATFORM"/headroom_ai-*.whl 2>/dev/null | head -1)"
if [[ -n "$WHEEL" ]]; then
  success "同梱のビルド済み wheel を使用: $(basename "$WHEEL")"
else
  warn "$PLATFORM 用のビルド済み wheel がありません"
  build_wheel || { fail "wheel を用意できませんでした。headroom 導入を中止します。"; exit 1; }
fi

# ── 2. 依存 + インストール & _core 確認 ──────────────────────────────────────
step "2. 依存とインストール"
HRVER="$(basename "$WHEEL" | sed -E 's/^headroom_ai-([0-9][^-]*)-.*/\1/')"
# proxy 実行に必要な純Python依存（fastapi/uvicorn/magika/zstandard/mcp/httpx[http2]/opentelemetry-api 等）
info "proxy 依存を導入中（数十MB・初回のみ）..."
"$PYTHON" -m pip install --user "headroom-ai[proxy]==$HRVER" >/dev/null 2>&1 \
  || "$PYTHON" -m pip install --user "headroom-ai[proxy]" >/dev/null 2>&1 \
  || warn "proxy 依存の導入で警告（後続を続行）"
# _core 入り wheel を最終的に上書き（PyPI の pure wheel が入っても _core 版を勝たせる）
"$PYTHON" -m pip install --user --force-reinstall --no-deps "$WHEEL" >/dev/null 2>&1 \
  && success "headroom-ai インストール完了（_core 入り wheel）" || { fail "pip install に失敗"; exit 1; }
if ( cd "$HOME" && "$PYTHON" -c "import headroom._core" >/dev/null 2>&1 ); then
  success "Rust 拡張 headroom._core OK"
else
  fail "headroom._core を import できません（wheel が _core 無しの可能性）"; exit 1
fi

# ── 4. ONNX runtime（load-dynamic 機種のみ）─────────────────────────────────
if [[ "$NEEDS_ONNX" -eq 1 ]]; then
  step "4. ONNX Runtime を配置"
  if [[ "$OS" == "Darwin" ]] && ensure_onnx_macos; then
    success "ONNX dylib: $ONNX_DIR/libonnxruntime.dylib"
  else
    warn "ONNX dylib を用意できませんでした。圧縮時に失敗する可能性があります。"
  fi
  export ORT_DYLIB_PATH="$ONNX_DIR/libonnxruntime.dylib"
fi

# ── 5. claude / codex をプロキシ経由に配線（headroom 自身の機能を利用）────────
step "5. claude / codex を配線"
export HEADROOM_TELEMETRY=off
# 5-1. 常駐サービス＋claude ルーティング（--providers auto は openclaw バグで死ぬので manual 固定）
"$HRBIN" install apply --providers manual --target claude --no-telemetry >/dev/null 2>&1 \
  && success "常駐プロキシ＋claude ルーティングを設定" || warn "install apply で警告"
# 5-2. codex ルーティング
"$HRBIN" init -g codex >/dev/null 2>&1 && success "codex ルーティングを設定" || warn "init codex で警告"
# 5-3. CCR 用 MCP retrieve（claude/codex 両方に登録）
"$HRBIN" mcp install >/dev/null 2>&1 && success "MCP retrieve を登録" || warn "mcp install で警告"

# 5-4. 常駐ラッパーに ORT_DYLIB_PATH を注入（次回ログイン/再起動でも ONNX を見つけるため）
WRAPPER="$HR_HOME/deploy/default/run-headroom.sh"
if [[ "$NEEDS_ONNX" -eq 1 && -f "$WRAPPER" ]] && ! grep -q "ORT_DYLIB_PATH" "$WRAPPER"; then
  "$PYTHON" - "$WRAPPER" "$ONNX_DIR/libonnxruntime.dylib" <<'PY'
import sys
p, dy = sys.argv[1], sys.argv[2]
s = open(p).read().splitlines()
out, injected = [], False
for ln in s:
    out.append(ln)
    if ln.startswith("set ") and not injected:
        out.append(f'export ORT_DYLIB_PATH="${{ORT_DYLIB_PATH:-{dy}}}"')
        injected = True
if not injected:
    out.insert(1, f'export ORT_DYLIB_PATH="${{ORT_DYLIB_PATH:-{dy}}}"')
open(p, "w").write("\n".join(out) + "\n")
PY
  success "常駐ラッパーに ORT_DYLIB_PATH を注入"
fi

# 5-5. MCP 起動コマンドを絶対パス化（headroom が PATH 外でも起動できるように）
"$PYTHON" - "$HRBIN" "${ORT_DYLIB_PATH:-}" <<'PY'
import json, os, sys
hrbin = sys.argv[1]; dy = sys.argv[2]
# claude.json
cp = os.path.expanduser("~/.claude.json")
if os.path.exists(cp):
    try:
        d = json.load(open(cp)); n = 0
        def walk(o):
            global n
            if isinstance(o, dict):
                m = o.get("mcpServers")
                if isinstance(m, dict) and "headroom" in m:
                    h = m["headroom"]; h["command"] = hrbin
                    h.setdefault("env", {})
                    if dy: h["env"]["ORT_DYLIB_PATH"] = dy
                    h["env"]["HEADROOM_TELEMETRY"] = "off"; n += 1
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for x in o: walk(x)
        walk(d)
        if n: json.dump(d, open(cp, "w"), indent=2)
    except Exception as e:
        print("claude.json patch skipped:", e)
# codex config.toml
tp = os.path.expanduser("~/.codex/config.toml")
if os.path.exists(tp):
    s = open(tp).read()
    s2 = s.replace('command = "headroom"', f'command = "{hrbin}"')
    if s2 != s: open(tp, "w").write(s2)
PY
success "MCP 起動コマンドを絶対パス化"

# 5-6. PATH に headroom bin を追記（手動マーカーで headroom 管理ブロックと分離）
add_path_block() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  grep -q "headroom extra (team-info)" "$f" 2>/dev/null && return 0
  printf '\n# >>> headroom extra (team-info) >>>\nexport PATH="%s:$PATH"\n# <<< headroom extra (team-info) <<<\n' "$PY_BIN_DIR" >> "$f"
}
for rc in "$HOME/.zshrc" "$HOME/.zprofile" "$HOME/.bashrc" "$HOME/.profile"; do add_path_block "$rc"; done
success "PATH に headroom bin を追記"

# サービス再起動（ラッパーの ORT を反映）
if [[ "$OS" == "Darwin" ]]; then
  launchctl kickstart -k "gui/$(id -u)/com.headroom.default" >/dev/null 2>&1 || true
fi

# ── 6. 動作確認 ─────────────────────────────────────────────────────────────
step "6. 動作確認"
PORT="${HEADROOM_PORT:-8787}"
ok=0
for _ in $(seq 1 25); do
  if curl -s -m 3 "http://127.0.0.1:${PORT}/readyz" >/dev/null 2>&1; then ok=1; break; fi
  sleep 2
done
if [[ "$ok" -eq 1 ]]; then
  state="$(curl -s -m5 "http://127.0.0.1:${PORT}/readyz" 2>/dev/null | "$PYTHON" -c "import sys,json;d=json.load(sys.stdin);print('ready=%s rust_core=%s'%(d.get('ready'),d.get('rust_core')))" 2>/dev/null)"
  success "プロキシ稼働中: $state"
  echo ""
  success "Headroom 導入完了。新しいターミナルから claude / codex がプロキシ経由になります。"
  info  "節約レポート: bash \"$REPO_ROOT/setup/headroom/check.sh\""
else
  warn "プロキシの起動を確認できませんでした。ログ: ~/.headroom/deploy/default/ を確認してください。"
  exit 1
fi
