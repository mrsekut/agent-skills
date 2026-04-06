# AI-Friendly CLI パターン詳細

各パターンの実装方法、テンプレート、具体例をまとめたリファレンス。

---

## 1. Claude Code SKILL.md

### なぜ最優先か

SKILL.mdはClaude Codeがツールを使い始めるとき最初に読むファイル。
これがあるとAIは「このツールで何ができて、どう使うべきか」を理解した状態で作業を始められる。
逆にこれがないと、AIはREADMEを読んだり`--help`を叩いたりして手探りで使い方を学ぶことになり、
コンテキストと時間を大量に消費する。

### 配布モデル

ツールのリポジトリにスキルを同梱し、ユーザーにインストールさせる。

**推奨ディレクトリ構成:**

```
my-tool/
├── src/              # ツール本体
├── skills/           # Claude Code向けスキル（配布用）
│   └── my-tool/
│       ├── SKILL.md
│       ├── README.md       # インストール手順（人間向け）
│       └── references/     # 詳細ドキュメント（必要に応じて）
└── README.md
```

**インストール方法:**

skills.sh を使うと簡単にインストールできる:

```bash
npx skills add owner/repo
```

手動の場合はリポジトリからスキルディレクトリを `~/.claude/skills/` にコピーする。

README.mdにインストール手順を書いておくこと。
スキルはツールと一緒にバージョン管理され、ツールの更新に合わせてスキルも更新される。

### テンプレート

以下の構成をベースに、ツールの実際のコマンドに置き換えて書く。
`{...}` はプレースホルダー。

```markdown
---
name: { ツール名 }
description: >
  {1-3行でツールの説明}。
  {トリガー条件。具体的なユーザー発話フレーズを列挙する}。
---

# {ツール名}

{1-2行でツールの目的}

## コマンドリファレンス

### よく使うコマンド

{テーブル形式で、AIが頻繁に使うコマンドを列挙}

### 全コマンド一覧

{全コマンドをカテゴリ別にまとめる}

## ワークフロー

{典型的な使い方をステップバイステップで示す}

## エラー時

{よくあるエラーコードと対処法}

## 注意事項

- {インタラクティブなコマンドがあれば警告}
- {やってはいけない操作}
```

### description（トリガー条件）の書き方

descriptionはClaude Codeがスキルを使うかどうかを判断する唯一の手がかり。
具体的なユーザー発話パターンを含めると、適切にトリガーされやすくなる。

**良い例:**

```yaml
description: >
  プロジェクトのタスク管理ツール。タスクの作成・一覧・更新・完了を行う。
  「タスクを作って」「何をやるべき?」「このissueを閉じて」「進捗は?」
  といった場面で使うこと。タスクやissueに言及したら積極的に使う。
```

**悪い例:**

```yaml
description: A task management tool.
```

### Hooks の設定

SKILL.mdと一緒に `.claude/settings.json` も整備する。

**SessionStart hook** — セッション開始時にコンテキストを注入:

```json
{
	"hooks": {
		"SessionStart": [
			{
				"type": "command",
				"command": "mytool prime"
			}
		]
	}
}
```

`prime` コマンド（または `mytool context`、`mytool status` など）を実装して、
「今の状態」「やるべきこと」「利用可能なコマンド」を短くまとめて出力する。
出力量はコンパクトに（500トークン以内が目安）。

**PreToolUse hook** — 危険な操作をブロック:

```json
{
	"hooks": {
		"PreToolUse": [
			{
				"matcher": "Bash",
				"hooks": [
					{
						"type": "command",
						"command": ".claude/hooks/block-interactive-cmds.sh"
					}
				]
			}
		]
	}
}
```

ブロック対象の例:

- インタラクティブコマンド（`vim`, `nano`, `less`）
- 破壊的操作のうち特にリスクが高いもの
- APIレート制限に引っかかるポーリング系

---

## 2. 構造化出力

### なぜ必要か

AIエージェントは `grep` や正規表現でテキスト出力をパースすることもできるが、
フォーマットが少しでも変わると壊れる。JSONなら確実にパースでき、フィールドの追加にも強い。

### 実装パターン

- ルートコマンドにグローバル `--json` フラグを追加する
- 各コマンドで個別にJSON分岐を書くのではなく、共通の出力ヘルパー関数を用意する
  - `--json` あり → JSON出力、なし → 従来のhuman-readable出力
- JSONは `stdout` に、ログや警告は `stderr` に出す（AIは `stdout` だけをパースする）

### エラー出力もJSON化する

```json
{
	"error": "issue not found: bd-xyz",
	"hint": "Use 'mytool list' to see available items",
	"code": "NOT_FOUND"
}
```

エラーコードは機械判定用、hintはAIが次のアクションを決めるためのもの。
この2つを分けることで、AIはエラーコードで分岐しつつ、hintを参考に復旧できる。

### 注意点

- human-readable出力は削除しない。`--json` がないときは従来通りの表示を維持する
- JSONスキーマは安定させる。フィールドの削除は破壊的変更として扱う
- stderrにはログや警告を出してよい（AIはstdoutだけをパースする）

---

## 2. 非インタラクティブ設計

### なぜ必要か

AIエージェントはシェルコマンドを実行できるが、対話的な入力はできない。
`Enter your name:` のようなプロンプトが出ると、プロセスがハングする。

### 排除すべきパターン

| パターン           | 問題         | 代替                               |
| ------------------ | ------------ | ---------------------------------- |
| `$EDITOR` を起動   | AIが操作不能 | `--description` フラグで受け付ける |
| Y/n確認プロンプト  | ハング       | `--yes` / `--force` フラグ         |
| 対話的選択メニュー | ハング       | フラグで直接指定                   |
| ページャー（less） | ハング       | `--no-pager` または環境変数        |
| パスワード入力     | ハング       | 環境変数 or `--token` フラグ       |

### stdinからの入力

長いテキスト（説明文など）はstdinで受け付けると便利:

```bash
echo "長い説明文" | mytool update item-1 --description=-
cat description.md | mytool update item-1 --description=-
```

`-` はstdinから読むことを示す一般的な慣習。

### 既存のインタラクティブ機能を残す場合

人間向けのインタラクティブUIは残してよいが、
非インタラクティブな代替手段を必ず用意する:

```bash
mytool edit item-1           # 人間向け: エディタが開く
mytool update item-1 --description "text"  # AI向け: フラグで完結
```

---

## 3. AI向けドキュメント

### AGENT_INSTRUCTIONS.md

AIエージェントがこのツールを使うときの操作マニュアル。
README.mdとは別に作る（READMEは人間向け、AGENT_INSTRUCTIONSはAI向け）。

**テンプレート:**

```markdown
# {ツール名} - Agent Instructions

## Quick Start

{3-5行でツールの目的と基本的な使い方}

## コマンドリファレンス

### よく使うコマンド

{AIが最も頻繁に使うコマンドを優先的に}

### 全コマンド一覧

{コマンド、フラグ、出力形式の一覧}

## ワークフロー

### 基本的な使い方

{ステップバイステップの手順}

### エラーが起きたとき

{よくあるエラーと対処法}

## 注意事項

- {やってはいけないこと}
- {ハマりやすいポイント}
```

### ポイント

- **コマンド例は必ずコピペ可能にする** — AIはサンプルコマンドをそのまま実行する
- **出力例も載せる** — AIが期待する出力形式を知ることで、正しくパースできる
- **「やるべきこと」と「やってはいけないこと」を明示する**
- 曖昧な表現（「適宜」「必要に応じて」）を避け、具体的な条件を書く

### CLIヘルプの改善

`--help` の出力もAIにとって重要な情報源。以下を意識する:

```
Usage: mytool create [flags]

Create a new item.

Flags:
  --title string       Item title (required)
  --type string        Item type: task, bug, feature (default "task")
  --priority int       Priority 0-4 (0=critical, 4=backlog) (default 2)
  --json               Output in JSON format

Examples:
  mytool create --title "Fix login bug" --type bug --priority 1
  mytool create --title "Add search" --type feature --json
```

- `(required)` を明示する
- 選択肢がある場合は列挙する
- デフォルト値を書く
- 実行可能なExamplesを載せる

---

## 4. エラーハンドリング

### 3段階分類

| レベル | いつ                     | 振る舞い          | 例                     |
| ------ | ------------------------ | ----------------- | ---------------------- |
| Fatal  | 回復不能                 | stderr + exit(1)  | 不正な入力、DB接続失敗 |
| Warn   | オプショナルな機能が失敗 | stderr + 処理続行 | 設定ファイル作成失敗   |
| Silent | クリーンアップ系         | 出力なし          | 一時ファイル削除失敗   |

### JSON出力時のエラー形式

```json
{
	"error": "具体的なエラーメッセージ",
	"code": "MACHINE_READABLE_CODE",
	"hint": "次にやるべきアクションの提案"
}
```

**良いhintの例:**

- `"Use 'mytool list' to see available items"`
- `"Check if the file exists with 'ls path/to/file'"`
- `"Run 'mytool init' to set up the workspace"`

**悪いhintの例:**

- `"Something went wrong"` （何もわからない）
- `"Please try again"` （同じことをしても直らない）

### 終了コードの一貫性

```
0: 成功
1: 一般的なエラー
2: 使い方の間違い（不正なフラグなど）
```

AIは終了コードで成功/失敗を判定する。0以外はすべてエラーとして扱う。

---

## 5. コンテキスト最適化

### なぜ必要か

AIのコンテキストウィンドウは有限。100件のアイテムを全フィールド付きで返すと、
それだけで数千トークンを消費し、他の作業に使えるコンテキストが減る。

### 段階的な情報提供

3段階のモデルを用意する:

```
Brief  (~20 bytes/item): id, title, status
Normal (~80 bytes/item): + assignee, labels, 関連数
Full   (~400+ bytes/item): + description, comments, 全フィールド
```

実装例:

```bash
mytool list                    # Normal（デフォルト）
mytool list --brief            # Brief
mytool show item-1             # Full（単一アイテム）
mytool list --fields id,title  # カスタム
```

### 自動コンパクション

結果が多いときに自動的にコンパクトする:

```bash
# 20件以上なら自動的にbrief表示 + 件数サマリー
mytool list --json
{
  "total": 47,
  "showing": "brief",
  "items": [
    {"id": "item-1", "title": "...", "status": "open"},
    ...
  ],
  "hint": "Use 'mytool show <id> --json' for full details"
}
```

### 環境変数によるチューニング

```bash
export MYTOOL_COMPACTION_THRESHOLD=20  # 自動コンパクションの閾値
export MYTOOL_DEFAULT_FORMAT=brief     # デフォルト出力形式
```

---

## チェックリスト

改善の進捗確認に使える。すべてを満たす必要はなく、ツールの性質に応じて取捨選択する。

### 必須（ほぼ全てのAI向けCLIで必要）

- [ ] Claude Code向けのSKILL.mdがある
- [ ] すべてのコマンドが `--json` で構造化出力を返す
- [ ] エラー出力もJSON（`--json` 時）
- [ ] インタラクティブな操作なしで全機能が使える
- [ ] `--help` にコピペ可能な実行例がある
- [ ] AGENT_INSTRUCTIONS.md がある

### 推奨（規模が大きくなったら）

- [ ] SessionStart hookでコンテキスト注入
- [ ] 危険操作をブロックするPreToolUse hook
- [ ] エラーにhintフィールドがある
- [ ] 出力の情報量を制御できる（brief/normal/full）

### 発展（マルチエージェント対応など）

- [ ] アトミック操作（claim/CAS）
- [ ] Actor tracking（誰が何をしたかの記録）
- [ ] 自動コンパクション
- [ ] stdinからの入力対応（長文テキスト用）
