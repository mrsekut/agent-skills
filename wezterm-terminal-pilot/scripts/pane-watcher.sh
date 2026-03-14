#!/bin/bash
# WezTermの全ペインの内容を定期的にファイルに書き出すバックグラウンドデーモン
# 使い方: cli-pilot/scripts/pane-watcher.sh &
# 停止: kill $(cat /tmp/wezterm-panes/watcher.pid)

DUMP_DIR="/tmp/wezterm-panes"
INTERVAL="${1:-2}"

# --- 起動時チェック ---

if ! command -v wezterm &>/dev/null; then
  echo "ERROR: wezterm コマンドが見つかりません" >&2
  exit 1
fi

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq コマンドが見つかりません。brew install jq でインストールしてください" >&2
  exit 1
fi

# --- 初期化 ---

mkdir -p "$DUMP_DIR"
echo $$ > "$DUMP_DIR/watcher.pid"

cleanup() {
  rm -f "$DUMP_DIR/watcher.pid"
  exit 0
}
trap cleanup EXIT INT TERM

# --- メインループ ---

while true; do
  # ペイン一覧をJSONで保存
  if wezterm cli list --format json > "$DUMP_DIR/panes.json.tmp" 2>/dev/null; then
    mv "$DUMP_DIR/panes.json.tmp" "$DUMP_DIR/panes.json"
  fi

  # 現在存在するペインIDの一覧を取得
  ACTIVE_PANES=$(jq -r '.[].pane_id' "$DUMP_DIR/panes.json" 2>/dev/null)

  # 各ペインの内容を個別ファイルに保存
  for pane_id in $ACTIVE_PANES; do
    wezterm cli get-text --pane-id "$pane_id" --start-line -200 > "$DUMP_DIR/$pane_id.txt" 2>/dev/null
  done

  # 古いペインファイルを削除（panes.jsonに存在しないペインの.txt）
  for txt_file in "$DUMP_DIR"/*.txt; do
    [ -f "$txt_file" ] || continue
    fname=$(basename "$txt_file" .txt)
    # 数字のみのファイル名（ペインID）のみ対象
    if [[ "$fname" =~ ^[0-9]+$ ]]; then
      if ! echo "$ACTIVE_PANES" | grep -qw "$fname"; then
        rm -f "$txt_file"
      fi
    fi
  done

  # タイムスタンプ更新
  date +%s > "$DUMP_DIR/last_update"

  sleep "$INTERVAL"
done
