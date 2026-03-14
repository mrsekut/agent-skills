---
name: wezterm-terminal-pilot
description: WezTermペインの読み取り・コマンド送信・ペイン管理・出力監視の統合ツール。「隣のペイン」「ペイン読んで」「コマンド送って」「隣で実行して」「ペインの内容」「テスト走らせて」「隣でビルドして」「ペイン分割して」「あっちの画面」「となりを見て」「ペイン2は？」と言われたら使う。
argument-hint: "[read|send|list|status] [pane-id] [command]"
---

WezTermの他のペインと協調して作業する統合ツール。
ペインの内容読み取り、コマンド送信、ペイン管理、出力監視を行う。

## アーキテクチャ

### pane-watcher デーモン

バックグラウンドで動作し、2秒間隔で全ペインの内容を `/tmp/wezterm-panes/` に書き出す。

**ファイル構成:**

- `/tmp/wezterm-panes/panes.json` — 全ペインのメタデータ（ID、タブ、CWD、アクティブ状態）
- `/tmp/wezterm-panes/{pane_id}.txt` — 各ペインの直近200行の内容
- `/tmp/wezterm-panes/watcher.pid` — デーモンのPID
- `/tmp/wezterm-panes/last_update` — 最終更新UNIXタイムスタンプ

### 起動方法

pane-watcher は初回操作時に自動起動する。手動起動も可能:

```bash
bash {{SKILL_PATH}}/scripts/pane-watcher.sh &
```

停止:

```bash
kill $(cat /tmp/wezterm-panes/watcher.pid)
```

## ペイン読み取り

### 手順

1. pane-watcher を確認・起動する

```bash
bash {{SKILL_PATH}}/scripts/cli-pilot.sh status
```

2. ペイン一覧を確認する

```bash
bash {{SKILL_PATH}}/scripts/cli-pilot.sh list
```

または `/tmp/wezterm-panes/panes.json` を Read ツールで読む。

3. 対象ペインの内容を読む

```bash
bash {{SKILL_PATH}}/scripts/cli-pilot.sh read [pane-id]
```

または `/tmp/wezterm-panes/{pane_id}.txt` を Read ツールで読む。

### ペインID省略時

ペインIDを省略すると自動選択される（後述の「ペイン選択ロジック」参照）。

### フォールバック

watcher が起動できない場合やファイルが存在しない場合:

```bash
wezterm cli list --format json                        # ペイン一覧
wezterm cli get-text --pane-id {ID} --start-line -200  # ペイン内容
```

### 内容の分析指針

取得したペイン内容は以下の方針で分析する:

- **コード**: 言語を推測し、シンタックスを理解した上で説明
- **コマンド出力・ログ**: 要点をまとめて説明
- **エラー**: 原因と解決策を提示
- **質問なし**: 内容の概要を簡潔に説明

## コマンド送信

### 基本

```bash
bash {{SKILL_PATH}}/scripts/send-command.sh <pane-id> <command>
```

例:

```bash
bash {{SKILL_PATH}}/scripts/send-command.sh 3 'npm test'
bash {{SKILL_PATH}}/scripts/send-command.sh 3 'git status'
bash {{SKILL_PATH}}/scripts/send-command.sh 3 'cd /path/to/project && ls'
```

### 安全チェック

send-command.sh は以下の安全チェックを行う:

- **自己ペイン保護**: `$WEZTERM_PANE` と同じペインへの送信を拒否
- **ペイン存在検証**: 送信先ペインが `panes.json` に存在するか確認

### 安全性分類

コマンドを送信する前に、以下の分類に従って判断する:

| Tier               | 動作                                 | 例                                                                                         |
| ------------------ | ------------------------------------ | ------------------------------------------------------------------------------------------ |
| Tier 1（安全）     | 即座に送信してよい                   | `ls`, `cat`, `pwd`, `git status`, `git diff`, `npm test`, `cd`, `echo`, `which`, `env`     |
| Tier 2（通知）     | 送信＋ユーザーに実行した旨を報告     | `npm install`, `git add`, `git commit`, `mkdir`, `touch`, `cp`, `mv`, `chmod`              |
| Tier 3（確認必須） | ユーザーの明示的な確認を得てから送信 | `rm`, `git push`, `git reset`, `sudo`, `kill`, `DROP TABLE`, `docker rm`, `brew uninstall` |

**ペイン管理操作の分類:**

- Tier 1: `split-pane`, `spawn`, `activate-pane`, `zoom-pane`, `adjust-pane-size`
- Tier 3: `kill-pane`

### 直接送信（スクリプト不使用）

特殊なケースではスクリプトを介さず直接送信も可能:

```bash
printf '%s\n' "command here" | wezterm cli send-text --pane-id <ID> --no-paste
```

**注意:** `--no-paste` は必須。省略するとブラケットペーストモードになり、シェルが実行しない場合がある。

## ペイン管理

### ペインの分割

```bash
# 右に分割（デフォルト）
wezterm cli split-pane

# 下に分割
wezterm cli split-pane --bottom

# サイズ指定
wezterm cli split-pane --bottom --percent 30

# 特定ディレクトリで分割
wezterm cli split-pane --cwd /path/to/dir
```

分割コマンドは新しいペインのIDを標準出力に返す。

### 新しいタブ/ウィンドウ

```bash
wezterm cli spawn           # 新しいタブ
wezterm cli spawn --new-window  # 新しいウィンドウ
```

### ペインの終了（Tier 3: 確認必須）

```bash
wezterm cli kill-pane --pane-id <ID>
```

### リサイズ

```bash
wezterm cli adjust-pane-size --pane-id <ID> --amount 5 Up
wezterm cli adjust-pane-size --pane-id <ID> --amount 5 Down
wezterm cli adjust-pane-size --pane-id <ID> --amount 10 Left
wezterm cli adjust-pane-size --pane-id <ID> --amount 10 Right
```

### ズーム

```bash
wezterm cli zoom-pane --pane-id <ID> --zoom
wezterm cli zoom-pane --pane-id <ID> --unzoom
```

### フォーカス移動

```bash
wezterm cli activate-pane --pane-id <ID>
wezterm cli activate-pane-direction Right
```

### ペインの移動

```bash
wezterm cli move-pane-to-new-tab --pane-id <ID>
```

## 出力監視

コマンド送信後、出力を監視して完了を検出する手順。

### 手順

1. **送信前**: 対象ペインの現在の内容を Read で記録（ベースライン）
2. **コマンド送信**: `send-command.sh` で送信
3. **ポーリング**: 一定間隔でペインの内容を Read して変化を確認
4. **完了検出**: 以下のいずれかで完了と判断
5. **結果報告**: ユーザーに要約を伝える

### 完了検出の判断基準

- **シェルプロンプト再出現**: `$`, `%`, `>`, `❯` などのプロンプトパターンが末尾に出現
- **特定パターン**: `PASS`, `FAIL`, `error`, `Error`, `BUILD SUCCESSFUL`, `exit code` など
- **出力安定化**: 2回連続で内容が同じなら完了とみなす

### ポーリング間隔の目安

| タスク種別 | 間隔     | 例                                    |
| ---------- | -------- | ------------------------------------- |
| 短タスク   | 3〜5秒   | `ls`, `git status`, `cat`             |
| 中タスク   | 5〜10秒  | `npm test`, `cargo build`, `go test`  |
| 長タスク   | 10〜15秒 | `npm install`, `docker build`, CI実行 |

### タイムアウト

約120秒で中間報告し、続行するかユーザーに確認する。

### 実装例

```
1. Read /tmp/wezterm-panes/{pane_id}.txt  (ベースライン記録)
2. bash send-command.sh {pane_id} 'npm test'
3. sleep 5
4. Read /tmp/wezterm-panes/{pane_id}.txt  (変化確認)
5. 完了していなければ 3 に戻る
6. 差分を抽出してユーザーに報告
```

## ペアプログラミングパターン

### パターン1: テスト実行 & 修正

1. ユーザー「テスト走らせて」
2. 隣のペインにテストコマンドを送信
3. 出力を監視、完了を待つ
4. 結果を読み取り、失敗があれば修正を提案/実行

### パターン2: ビルド監視

1. ユーザー「ビルドして」
2. ペインにビルドコマンドを送信
3. 出力をポーリングで監視
4. エラーがあれば原因と修正を提示

### パターン3: サーバー起動 & 確認

1. ペインにサーバー起動コマンドを送信
2. 起動完了を監視（`listening on port` 等のパターン）
3. 起動完了をユーザーに報告

### パターン4: 対話的デバッグ

1. ペインの内容を読み、エラーや状態を確認
2. 原因を分析し、修正コマンドを送信
3. 結果を確認、必要なら繰り返す

### パターン5: 隣のペインの状況把握

1. ユーザー「隣で何やってる？」
2. ペインの内容を読み取り
3. 実行中のプロセス、出力内容、エラー有無を要約

## ペイン選択ロジック

全機能共通のペイン自動選択アルゴリズム。引数でペインIDが指定されていない場合に使われる。

**優先順位:**

1. **引数指定**: ペインIDが明示的に渡されていればそれを使う
2. **同一タブの兄弟ペイン**: `$WEZTERM_PANE` と同じ `tab_id` を持つ別のペインを選ぶ
3. **非アクティブペイン**: `is_active: false` のペインを選ぶ
4. **直接CLI**: `wezterm cli list` から非アクティブペインを取得

**ペインが見つからない場合:**
ペインが存在しない場合、分割を提案する:

```bash
wezterm cli split-pane
```

## エラーハンドリング

### よくあるエラーと対処法

| エラー                                     | 原因               | 対処                                           |
| ------------------------------------------ | ------------------ | ---------------------------------------------- |
| `wezterm コマンドが見つかりません`         | WezTerm外で実行    | WezTermのペイン内で実行する                    |
| `jq コマンドが見つかりません`              | jq未インストール   | `brew install jq`                              |
| `他のペインが見つかりません`               | ペインが1つだけ    | `wezterm cli split-pane` でペインを分割        |
| `ペイン N は存在しません`                  | ペインが閉じられた | `cli-pilot.sh list` で現在のペインを確認       |
| `自分のペインにはコマンドを送信できません` | 自ペインを指定     | 別のペインIDを指定する                         |
| watcher が起動しない                       | プロセス残存       | `rm /tmp/wezterm-panes/watcher.pid` して再起動 |
| データが古い                               | watcher停止        | `cli-pilot.sh status` で確認、必要なら再起動   |

### データ鮮度の確認

```bash
bash {{SKILL_PATH}}/scripts/cli-pilot.sh status
```

`last_update` が10秒以上前なら watcher を再起動する:

```bash
kill $(cat /tmp/wezterm-panes/watcher.pid) 2>/dev/null
bash {{SKILL_PATH}}/scripts/pane-watcher.sh &
```

## リファレンス

WezTerm CLIの全コマンド詳細は以下を参照:

- `{{SKILL_PATH}}/references/wezterm-cli-reference.md` — コマンド一覧、オプション、JSON出力スキーマ、エッジケース
