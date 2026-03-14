#!/bin/bash
# cli-pilot: WezTermペインの読み取り・一覧・ステータス確認
# 使い方:
#   cli-pilot.sh read [pane-id]   — ペインの内容を読み取る
#   cli-pilot.sh list             — ペイン一覧を表示
#   cli-pilot.sh status           — watcher と接続状態を表示

DUMP_DIR="/tmp/wezterm-panes"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- ヘルパー関数 ---

ensure_wezterm() {
  if ! command -v wezterm &>/dev/null; then
    echo "ERROR: wezterm コマンドが見つかりません" >&2
    exit 1
  fi
}

ensure_watcher() {
  # watcher が動いていなければ起動
  if [ ! -f "$DUMP_DIR/watcher.pid" ] || ! kill -0 "$(cat "$DUMP_DIR/watcher.pid" 2>/dev/null)" 2>/dev/null; then
    "$SCRIPT_DIR/pane-watcher.sh" &
    disown

    # 適応的待機: panes.json の出現をポーリング（0.5秒 × 最大10回）
    for i in $(seq 1 10); do
      if [ -f "$DUMP_DIR/panes.json" ]; then
        return 0
      fi
      sleep 0.5
    done
    echo "WARN: watcher の初期化がタイムアウトしました。直接取得にフォールバックします" >&2
  fi
}

select_pane() {
  local PANE_ID="$1"
  local MY_PANE="${WEZTERM_PANE:-}"

  # 1. 引数でペインIDが指定されていればそれを使う
  if [ -n "$PANE_ID" ]; then
    echo "$PANE_ID"
    return 0
  fi

  # 2. 同一タブの兄弟ペインを選ぶ
  if [ -n "$MY_PANE" ] && [ -f "$DUMP_DIR/panes.json" ]; then
    local MY_TAB
    MY_TAB=$(jq -r ".[] | select(.pane_id == $MY_PANE) | .tab_id" "$DUMP_DIR/panes.json" 2>/dev/null)
    if [ -n "$MY_TAB" ]; then
      local SIBLING
      SIBLING=$(jq -r "[.[] | select(.tab_id == $MY_TAB and .pane_id != $MY_PANE)][0].pane_id // empty" "$DUMP_DIR/panes.json" 2>/dev/null)
      if [ -n "$SIBLING" ]; then
        echo "$SIBLING"
        return 0
      fi
    fi
  fi

  # 3. 非アクティブなペインを選ぶ
  if [ -f "$DUMP_DIR/panes.json" ]; then
    local INACTIVE
    INACTIVE=$(jq -r "[.[] | select(.is_active == false)][0].pane_id // empty" "$DUMP_DIR/panes.json" 2>/dev/null)
    if [ -n "$INACTIVE" ]; then
      echo "$INACTIVE"
      return 0
    fi
  fi

  # 4. 直接CLIで取得を試みる
  local FALLBACK
  FALLBACK=$(wezterm cli list --format json 2>/dev/null | jq -r "[.[] | select(.is_active == false)][0].pane_id // empty")
  if [ -n "$FALLBACK" ]; then
    echo "$FALLBACK"
    return 0
  fi

  return 1
}

# --- サブコマンド ---

cmd_read() {
  local PANE_ID
  PANE_ID=$(select_pane "$1")

  if [ -z "$PANE_ID" ]; then
    echo "ERROR: 他のペインが見つかりません" >&2
    echo "ペインを分割してから再度実行してください:" >&2
    echo "  wezterm cli split-pane" >&2
    exit 1
  fi

  echo "=== Pane ID: $PANE_ID ==="
  echo ""

  # ファイルがあればファイルから読む、なければ直接取得
  if [ -f "$DUMP_DIR/$PANE_ID.txt" ]; then
    cat "$DUMP_DIR/$PANE_ID.txt"
  else
    wezterm cli get-text --pane-id "$PANE_ID" --start-line -200 2>/dev/null
  fi
}

cmd_list() {
  if [ -f "$DUMP_DIR/panes.json" ]; then
    local MY_PANE="${WEZTERM_PANE:-}"
    echo "=== ペイン一覧 ==="
    jq -r ".[] | \"  ID: \(.pane_id)\(.pane_id == ($MY_PANE | tonumber? // -1) | if . then \" (self)\" else \"\" end)  タブ: \(.tab_id)  タイトル: \(.title)  CWD: \(.cwd)  アクティブ: \(.is_active)\"" "$DUMP_DIR/panes.json" 2>/dev/null
  else
    echo "=== ペイン一覧 (直接取得) ==="
    wezterm cli list 2>/dev/null
  fi
}

cmd_status() {
  echo "=== cli-pilot ステータス ==="

  # wezterm 接続
  if command -v wezterm &>/dev/null; then
    echo "wezterm: OK"
  else
    echo "wezterm: NOT FOUND"
  fi

  # watcher 状態
  if [ -f "$DUMP_DIR/watcher.pid" ] && kill -0 "$(cat "$DUMP_DIR/watcher.pid" 2>/dev/null)" 2>/dev/null; then
    echo "watcher: 実行中 (PID: $(cat "$DUMP_DIR/watcher.pid"))"
  else
    echo "watcher: 停止"
  fi

  # データ鮮度
  if [ -f "$DUMP_DIR/last_update" ]; then
    local LAST_UPDATE NOW AGE
    LAST_UPDATE=$(cat "$DUMP_DIR/last_update")
    NOW=$(date +%s)
    AGE=$((NOW - LAST_UPDATE))
    echo "最終更新: ${AGE}秒前"
  else
    echo "最終更新: なし"
  fi

  # ペイン数
  if [ -f "$DUMP_DIR/panes.json" ]; then
    local COUNT
    COUNT=$(jq 'length' "$DUMP_DIR/panes.json" 2>/dev/null)
    echo "ペイン数: $COUNT"
  fi

  # 自分のペイン
  echo "自ペイン: ${WEZTERM_PANE:-不明}"
}

# --- メインディスパッチ ---

ensure_wezterm

SUBCMD="${1:-read}"
shift 2>/dev/null || true

case "$SUBCMD" in
  read)
    ensure_watcher
    cmd_read "$1"
    ;;
  list)
    ensure_watcher
    cmd_list
    ;;
  status)
    cmd_status
    ;;
  *)
    echo "使い方:" >&2
    echo "  cli-pilot.sh read [pane-id]   — ペインの内容を読み取る" >&2
    echo "  cli-pilot.sh list             — ペイン一覧を表示" >&2
    echo "  cli-pilot.sh status           — ステータスを表示" >&2
    exit 1
    ;;
esac
