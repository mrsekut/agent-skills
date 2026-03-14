#!/bin/bash
# 指定ペインにコマンドを送信するラッパースクリプト（安全チェック付き）
# 使い方: send-command.sh <pane-id> <command>

DUMP_DIR="/tmp/wezterm-panes"
PANE_ID="$1"
shift
COMMAND="$*"

# --- 引数チェック ---

if [ -z "$PANE_ID" ] || [ -z "$COMMAND" ]; then
  echo "使い方: send-command.sh <pane-id> <command>" >&2
  echo "例: send-command.sh 3 'ls -la'" >&2
  exit 1
fi

# --- 安全チェック ---

# 自己ペイン保護: 自分のペインへの送信を拒否
MY_PANE="${WEZTERM_PANE:-}"
if [ -n "$MY_PANE" ] && [ "$PANE_ID" = "$MY_PANE" ]; then
  echo "ERROR: 自分のペイン($MY_PANE)にはコマンドを送信できません" >&2
  exit 1
fi

# ペイン存在検証
if [ -f "$DUMP_DIR/panes.json" ]; then
  EXISTS=$(jq -r ".[] | select(.pane_id == $PANE_ID) | .pane_id" "$DUMP_DIR/panes.json" 2>/dev/null)
  if [ -z "$EXISTS" ]; then
    # panes.jsonが古い可能性があるので直接確認
    EXISTS=$(wezterm cli list --format json 2>/dev/null | jq -r ".[] | select(.pane_id == $PANE_ID) | .pane_id")
    if [ -z "$EXISTS" ]; then
      echo "ERROR: ペイン $PANE_ID は存在しません" >&2
      echo "利用可能なペイン:" >&2
      jq -r '.[] | "  ID: \(.pane_id)  タブ: \(.tab_id)  タイトル: \(.title)  アクティブ: \(.is_active)"' "$DUMP_DIR/panes.json" 2>/dev/null
      exit 1
    fi
  fi
else
  # panes.jsonがない場合は直接確認
  EXISTS=$(wezterm cli list --format json 2>/dev/null | jq -r ".[] | select(.pane_id == $PANE_ID) | .pane_id")
  if [ -z "$EXISTS" ]; then
    echo "ERROR: ペイン $PANE_ID は存在しません" >&2
    exit 1
  fi
fi

# --- コマンド送信 ---

printf '%s\n' "$COMMAND" | wezterm cli send-text --pane-id "$PANE_ID" --no-paste

if [ $? -eq 0 ]; then
  echo "OK: ペイン $PANE_ID に送信しました: $COMMAND"
else
  echo "ERROR: コマンド送信に失敗しました" >&2
  exit 1
fi
