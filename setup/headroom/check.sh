#!/usr/bin/env bash
# headroom 節約レポート（小学生むけ表示）
# 使い方: bash setup/headroom/check.sh
# 「前回このボタンを押してから、今回どれだけ言葉をへらせたか」を出します。
set -uo pipefail

PORT="${HEADROOM_PORT:-8787}"
SNAP="$HOME/.headroom/.last_snapshot.json"

# Python を決める（pyenv 3.11 優先 → python3）
PYTHON="${HEADROOM_PYTHON:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PYTHON="${2:-}"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ -z "${PYTHON}" || ! -x "${PYTHON}" ]]; then
  if command -v pyenv &>/dev/null; then
    _v="$(pyenv versions --bare 2>/dev/null | grep '^3\.11' | tail -1)"
    [[ -n "${_v}" ]] && PYTHON="$(pyenv root)/versions/${_v}/bin/python3"
  fi
fi
[[ -x "${PYTHON:-}" ]] || PYTHON="$(command -v python3 || true)"
[[ -x "${PYTHON:-}" ]] || { echo "python3 が見つかりません"; exit 1; }

TMP="$(mktemp "${TMPDIR:-/tmp}/hr_stats.XXXXXX")"
trap 'rm -f "$TMP"' EXIT
curl -s -m 8 "http://127.0.0.1:${PORT}/stats" -o "$TMP" 2>/dev/null
if [ ! -s "$TMP" ]; then
  echo "⚠️ 通訳さん（headroom）が今うごいていないみたいです。"
  echo "   少し待ってからもう一度ためしてください。"
  exit 0
fi

SNAP="$SNAP" STATS="$TMP" "$PYTHON" - <<'PY'
import json, os
d = json.load(open(os.environ["STATS"]))
s = d.get("summary", {})
agents = d.get("agent_usage", {}).get("agents", [])
before = sum(a.get("before_tokens", 0) for a in agents)
after  = sum(a.get("after_tokens", before) for a in agents)
saved  = sum(a.get("tokens_saved", 0) for a in agents)
reqs   = sum(a.get("requests", 0) for a in agents)
cache_usd = s.get("cost", {}).get("breakdown", {}).get("cache_savings_usd", 0) or 0

snap_path = os.environ["SNAP"]
prev = {}
if os.path.exists(snap_path):
    try: prev = json.load(open(snap_path))
    except Exception: prev = {}

def show(title, b, a, sv, rq, cu):
    pct = (sv / b * 100) if b else 0
    print(f"=== {title} ===")
    print(f"  AIとのやりとり: {rq} 回")
    print(f"  送った言葉    : {b:,} → {a:,} （{sv:,} 言葉をへらせた／{pct:.1f}%）")
    if cu and cu > 0:
        print(f"  キャッシュでの節約: 約 ${cu:.2f} 相当")
    if sv == 0 and (cu or 0) <= 0:
        print("  → 今回は へらせた言葉が ほぼ 0 でした。")
        print("     （短いやりとりだと へりにくいです。長い作業ほど効きます）")
    print()

# 前回からの差分（今回ぶん）
if prev:
    db = before - prev.get("before", 0)
    da = after  - prev.get("after", 0)
    ds = saved  - prev.get("saved", 0)
    dr = reqs   - prev.get("reqs", 0)
    dc = cache_usd - prev.get("cache_usd", 0)
    if dr > 0:
        show("前回チェックからの今回ぶん", db, da, ds, dr, dc)
    else:
        print("=== 前回チェックからの今回ぶん ===")
        print("  前回からまだ新しいやりとりがありません。")
        print("  claude や codex を使ってから、もう一度押してください。\n")

# ずっとの合計
show("通訳さんを雇ってからの合計", before, after, saved, reqs, cache_usd)

json.dump({"before":before,"after":after,"saved":saved,"reqs":reqs,"cache_usd":cache_usd},
          open(snap_path,"w"))
print("（このボタンを押した時点を記録しました。次に押すと『そこから今回ぶん』が出ます）")
PY
