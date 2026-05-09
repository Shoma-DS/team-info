#!/bin/bash
# Xプレビューサーバーを起動するスクリプト。
# ngrok で固定URL公開 → Python APIサーバー起動 → ブラウザ自動オープン。

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
PORT=8765
NGROK_DOMAIN="zinciferous-preludiously-draven.ngrok-free.dev"
PUBLIC_URL="https://${NGROK_DOMAIN}"

# 依存コマンドの確認
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 が見つかりません"; exit 1; }
command -v ngrok >/dev/null 2>&1 || { echo "❌ ngrok が見つかりません。brew install ngrok を実行してください"; exit 1; }

if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$REPO_ROOT/.env"
  set +a
fi

# NEON_DATABASE_URL の確認
if [ -z "$NEON_DATABASE_URL" ]; then
  echo "❌ NEON_DATABASE_URL が設定されていません"
  echo "   $REPO_ROOT/.env に NEON_DATABASE_URL=\"...\" を設定してください"
  exit 1
fi

echo "🚀 Xプレビューサーバーを起動します..."
echo "🔗 固定URL: ${PUBLIC_URL}"

# ------ 既存プロセスのクリーンアップ ------
EXISTING_PID=$(lsof -ti tcp:${PORT} 2>/dev/null || true)
if [ -n "$EXISTING_PID" ]; then
  echo "⚠️  ポート ${PORT} が使用中です。既存プロセス(PID: ${EXISTING_PID})を終了します..."
  kill "$EXISTING_PID" 2>/dev/null || true
  sleep 1
fi

# ngrok が既に動いていれば停止
pkill -f "ngrok http.*${NGROK_DOMAIN}" 2>/dev/null || true

# ------ ngrok でトンネル起動 ------
ngrok http --domain="${NGROK_DOMAIN}" "${PORT}" > /dev/null 2>&1 &
NGROK_PID=$!
sleep 2

# ------ Python プレビューサーバー起動 ------
export LT_PUBLIC_URL="${PUBLIC_URL}"
python3 "$SCRIPT_DIR/preview_server.py" &
SERVER_PID=$!

# サーバーが実際に起動するまで最大20秒待機
for i in $(seq 1 20); do
  sleep 1
  if lsof -ti tcp:${PORT} >/dev/null 2>&1; then
    echo "✅ プレビューサーバー起動: http://localhost:${PORT}"
    break
  fi
  if [ "$i" -eq 20 ]; then
    echo "❌ サーバーの起動に失敗しました (20秒タイムアウト)"
    kill "$NGROK_PID" 2>/dev/null || true
    exit 1
  fi
done

# ブラウザを開く
echo "🖥  ブラウザを開いています..."
if command -v open >/dev/null 2>&1; then
  open "http://localhost:${PORT}"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://localhost:${PORT}"
fi

echo ""
echo "✅ 起動完了"
echo "   ローカル : http://localhost:${PORT}"
echo "   スマホ等 : ${PUBLIC_URL}"
echo ""
echo "   終了するには Ctrl+C を押してください"

# Ctrl+C で両プロセスを停止
cleanup() {
  echo ""
  echo "🛑 停止中..."
  kill "$SERVER_PID" 2>/dev/null || true
  kill "$NGROK_PID" 2>/dev/null || true
  echo "サーバーを停止しました"
}
trap cleanup INT TERM

wait "$SERVER_PID"
