# WezTerm CLI リファレンス

WezTerm のターミナルマルチプレクサ機能を CLI から操作するためのコマンド一覧。

## 前提

- `wezterm cli` サブコマンドは、WezTerm 内のペインから実行する必要がある
- 環境変数 `$WEZTERM_UNIX_SOCKET` が設定されていること（WezTerm内では自動設定）
- 環境変数 `$WEZTERM_PANE` で自分のペインIDを取得できる

## コマンド一覧

### list — ペイン一覧の取得

```bash
wezterm cli list                 # テーブル形式
wezterm cli list --format json   # JSON形式（スクリプト向け）
```

**JSON出力スキーマ:**

```json
[
  {
    "window_id": 0,
    "tab_id": 0,
    "tab_title": "tab-title",
    "pane_id": 0,
    "workspace": "default",
    "size": { "rows": 24, "cols": 80, "pixel_width": 640, "pixel_height": 480, "dpi": 96 },
    "title": "zsh",
    "cwd": "file:///Users/user/project",
    "cursor_x": 0,
    "cursor_y": 23,
    "cursor_shape": "Default",
    "cursor_visibility": "Visible",
    "left_col": 0,
    "top_row": 0,
    "is_active": true,
    "is_zoomed": false,
    "tty_name": "/dev/ttys001"
  }
]
```

**主要フィールド:**

| フィールド | 用途 |
|-----------|------|
| `pane_id` | ペイン操作の対象指定 |
| `tab_id` | 同一タブのペインをグループ化 |
| `is_active` | 現在フォーカスがあるか |
| `cwd` | ペインの作業ディレクトリ（`file://` プレフィックス付き） |
| `title` | 実行中のプロセス名 |
| `cursor_x`, `cursor_y` | カーソル位置 |

### get-text — ペイン内容の取得

```bash
# 直近200行を取得（推奨）
wezterm cli get-text --pane-id <ID> --start-line -200

# 全内容を取得
wezterm cli get-text --pane-id <ID>

# 範囲指定
wezterm cli get-text --pane-id <ID> --start-line 0 --end-line 50

# --escapes: ANSIエスケープシーケンスを保持
wezterm cli get-text --pane-id <ID> --escapes
```

**注意:**
- `--start-line` に負の値を指定するとスクロールバック末尾からの相対行数
- `--pane-id` を省略すると自分のペインが対象になる
- 出力にはANSIカラーコードは含まれない（`--escapes` 指定時を除く）

### send-text — ペインへのテキスト送信

```bash
# パイプで送信（推奨）
printf '%s\n' "ls -la" | wezterm cli send-text --pane-id <ID> --no-paste

# 引数で送信（非推奨: クォートが複雑になる）
wezterm cli send-text --pane-id <ID> "ls -la\n"
```

**オプション:**

| オプション | 説明 |
|-----------|------|
| `--pane-id <ID>` | 送信先ペインID |
| `--no-paste` | ブラケットペーストモードを使わずに送信（コマンド実行向け） |

**注意:**
- `--no-paste` を付けないとブラケットペーストとして送信され、シェルが実行せず貼り付けとして扱う場合がある
- 改行（`\n`）を含めないとコマンドが実行されない
- `printf '%s\n' "command" | wezterm cli send-text --pane-id <ID> --no-paste` がクォート問題を最も回避できるパターン

### split-pane — ペインの分割

```bash
# 右に分割（デフォルト）
wezterm cli split-pane --pane-id <ID>

# 下に分割
wezterm cli split-pane --pane-id <ID> --bottom

# 左に分割
wezterm cli split-pane --pane-id <ID> --left

# 上に分割
wezterm cli split-pane --pane-id <ID> --top

# サイズ指定（パーセンテージ）
wezterm cli split-pane --pane-id <ID> --bottom --percent 30

# コマンドを指定して分割
wezterm cli split-pane --pane-id <ID> -- bash -c "npm test"

# 作業ディレクトリを指定
wezterm cli split-pane --pane-id <ID> --cwd /path/to/dir
```

**出力:** 新しく作成されたペインのIDが返る

### spawn — 新しいペイン/タブ/ウィンドウの生成

```bash
# 新しいタブを生成
wezterm cli spawn

# 新しいウィンドウを生成
wezterm cli spawn --new-window

# コマンドを指定
wezterm cli spawn -- bash -c "htop"

# 作業ディレクトリを指定
wezterm cli spawn --cwd /path/to/dir
```

**出力:** 新しく作成されたペインのIDが返る

### kill-pane — ペインの終了

```bash
wezterm cli kill-pane --pane-id <ID>
```

**注意:** 自分のペインを kill すると接続が切れる

### activate-pane — ペインへのフォーカス移動

```bash
# 特定のペインにフォーカス
wezterm cli activate-pane --pane-id <ID>

# 方向でフォーカス移動
wezterm cli activate-pane-direction Up
wezterm cli activate-pane-direction Down
wezterm cli activate-pane-direction Left
wezterm cli activate-pane-direction Right
```

### adjust-pane-size — ペインサイズの変更

```bash
# 方向を指定してリサイズ（セル単位）
wezterm cli adjust-pane-size --pane-id <ID> --amount 5 Up
wezterm cli adjust-pane-size --pane-id <ID> --amount 5 Down
wezterm cli adjust-pane-size --pane-id <ID> --amount 10 Left
wezterm cli adjust-pane-size --pane-id <ID> --amount 10 Right
```

### zoom-pane — ペインのズーム切り替え

```bash
# ズームをトグル
wezterm cli zoom-pane --pane-id <ID>

# ズームを解除
wezterm cli zoom-pane --pane-id <ID> --unzoom

# ズームする
wezterm cli zoom-pane --pane-id <ID> --zoom
```

### move-pane-to-new-tab — ペインを新しいタブに移動

```bash
wezterm cli move-pane-to-new-tab --pane-id <ID>

# 別のウィンドウのタブに移動
wezterm cli move-pane-to-new-tab --pane-id <ID> --window-id <WINDOW_ID>
```

### activate-tab — タブの切り替え

```bash
# タブインデックスで切り替え（0始まり）
wezterm cli activate-tab --tab-index 0

# 相対移動
wezterm cli activate-tab --tab-relative 1   # 次のタブ
wezterm cli activate-tab --tab-relative -1  # 前のタブ
```

### set-tab-title — タブタイトルの設定

```bash
wezterm cli set-tab-title "My Tab" --pane-id <ID>
```

### set-window-title — ウィンドウタイトルの設定

```bash
wezterm cli set-window-title "My Window" --window-id <ID>
```

## エッジケースと注意点

1. **ペインIDの寿命**: ペインが閉じられるとIDは無効になる。操作前に `list` で存在確認を推奨
2. **ソケット接続**: `$WEZTERM_UNIX_SOCKET` が未設定の環境（SSH先など）では動作しない
3. **send-text の改行**: `\n` を末尾に含めないとコマンドが入力されるだけで実行されない
4. **get-text の空行**: 出力末尾に空行が大量に含まれる場合がある
5. **cwd の形式**: `file:///path` 形式。パスとして使う場合はプレフィックスを除去する必要がある
6. **split-pane のサイズ制限**: ペインが小さすぎると分割に失敗する
7. **並行操作**: 複数プロセスが同時にペイン操作すると競合する可能性がある
