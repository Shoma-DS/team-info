#!/bin/bash
# Xプレビューサーバーを起動するスクリプト。
# ngrok で固定URL公開 → Python APIサーバー起動 → ブラウザ自動オープン。

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8765
NGROK_DOMAIN="zinciferous-preludiously-draven.ngrok-free.dev"
PUBLIC_URL="https://${NGROK_DOMAIN}"

# 依存コマンドの確認
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 が見つかりません"; exit 1; }
command -v ngrok >/dev/null 2>&1 || { echo "❌ ngrok が見つかりません。brew install ngrok を実行してください"; exit 1; }

# NEON_DATABASE_URL の確認
if [ -z "$NEON_DATABASE_URL" ]; then
  echo "❌ NEON_DATABASE_URL が設定されていません"
  echo "   ~/.zshrc に export NEON_DATABASE_URL=\"...\" を追加して source ~/.zshrc を実行してください"
  exit 1
fi

echo "🚀 Xプレビューサーバーを起動します..."
echo "🔗 固定URL: ${PUBLIC_URL}"

# ------ ngrok でトンネル起動 ------
ngrok http --domain="${NGROK_DOMAIN}" "${PORT}" > /dev/null 2>&1 &
NGROK_PID=$!
sleep 2

# ------ Python プレビューサーバー起動 ------
export LT_PUBLIC_URL="${PUBLIC_URL}"
python3 "$SCRIPT_DIR/preview_server.py" &
SERVER_PID=$!
sleep 1

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
