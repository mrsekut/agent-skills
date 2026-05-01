---
name: claude-session-finder
description: 過去のClaude Codeセッションを内容ベースで検索して、resume用のsession IDを返すスキル。「あの会話どこだっけ」「過去のセッション探して」「〇〇の話してたセッション見つけて」「前にやってた△△の続きやりたい」「うろ覚えだけど〜の会話を探したい」と言われたら使う。タイトルや断片的なキーワードしか覚えていない会話を、内容のgrep + 中身を読んでの再ランクで発掘する。`claude -r` の標準resumeでは見つけにくい古い会話を掘り起こすために積極的に使うこと。
argument-hint: "検索クエリ [--cwd]"
---

# Claude Session Finder

`~/.claude/projects/**/*.jsonl` を走査し、ユーザーがうろ覚えの過去会話を発掘して `claude -r` で再開できる session ID を返すスキル。

## 何をするか

1. 検索クエリで grep して候補ファイルを絞る
2. 上位候補の中身を読んで意味的に再ランクする
3. session ID + プロジェクト + 日付 + 1行要約 + ヒット箇所の引用 を返す
4. ユーザーが選んだら `claude -r <id>` の実行を提案する（勝手には実行しない）

## ストレージ構造の前提

- メインセッション: `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`
- サブエージェント: `~/.claude/projects/<encoded-cwd>/<session-id>/subagents/*.jsonl` ← 対象外
- `encoded-cwd` は cwd の `/` を `-` に置換したもの（例: `/Users/foo/bar` → `-Users-foo-bar`）
- session ID = ファイル名から `.jsonl` を除いたもの
- プロジェクト名 = encoded-cwd の最後のセグメント

JSONL の各行は `{"sessionId":..., "cwd":..., "type":"user"|"assistant", "message":{"role":..., "content":...}, "timestamp":..., ...}` の形。

## 手順

### 1. クエリの解釈

引数からクエリと `--cwd` フラグを抽出。クエリは「React Server Components」のような単語列でも「Linearで詰まった件」のような自然文でもよい。自然文ならキーワードを 2-4 個に分解して OR 検索する。

### 2. grep で候補を絞る

Grep tool で:

- `path`: `--cwd` 指定時は `~/.claude/projects/<encoded-current-cwd>/`、それ以外は `~/.claude/projects/`
- `glob`: `*.jsonl`（subagent サブディレクトリ配下も拾うので、ヒット後にパス階層で除外する）
- `pattern`: 抽出したキーワード（複数なら `keyword1|keyword2`）
- `-i: true`, `output_mode: "files_with_matches"`, `head_limit: 50`

ヒットしたパスのうち `/<id>/subagents/` を含むものは捨てる（メインセッションのみ残す）。

### 3. mtime で時系列ソート + 上位選抜

候補が 10 件以上なら Bash で `ls -lt` 相当を取って新しい順にし、上位 8-12 件に絞る。Recency バイアスを入れる理由: 古いセッションは記憶が薄れていてもユーザーが探したいのはたいてい最近のもの。ただし「昔の」「数ヶ月前」のような表現があれば古い方も残す。

### 4. 中身を読んで再ランク

各候補について:

- Read で先頭 80 行ほど読み、最初のユーザープロンプトと初期の assistant 応答から「何の話か」を把握
- Grep でヒット行周辺（`-C 5`）を見て、キーワードが本題なのか脱線で出ただけなのかを判断
- 1 行要約 + 代表的な引用 1 つ + 日付（ファイル mtime か最初の `timestamp` フィールド）を抽出

クエリとの意味的近さで再ランクする。grep が語彙ミスマッチで取りこぼしてそうなら別キーワードで再検索する（例: 「ベクトル検索」がヒット 0 → 「embedding」「semantic search」で再試行）。

### 5. 出力

各セッションごとに、メタ情報を plain text の行として並べ、その下に resume コマンドを **top-level の fenced code block** (` ```bash ... ``` `) として出す。

**重要な見た目ルール**:

- メタ情報を `-` の箇条書きにしない。`-` リストにすると code block をリスト内にネストせざるを得ず、`/copy` (claude-code-copy-markdown) でコピー単位として認識されなくなる
- 各メタ行は絵文字プレフィックス + 内容で 1 行ずつ並べる（インデントなし）
- code block は左端揃え（インデントなし）で出す。これでコピー選択肢として独立認識される
- メタ行と code block の間は空行を入れず詰めて出すことで、視覚的にそのエントリの一部として見える

````
🔍 "<クエリ>" にマッチしたセッション (上位N件)

**1.** `0e68d2f3-3361-4991-b23c-8adc4d0d2536`
📁 zatsu (/Users/mrsekut/Desktop/dev/github.com/mrsekut/zatsu)
📅 2026-04-12
💬 React Server Components のレンダリングモデルとSSRとの違いを議論
📌 "RSC では client/server の境界がコンポーネント単位で..."
```bash
cd /Users/mrsekut/Desktop/dev/github.com/mrsekut/zatsu && claude -r 0e68d2f3-3361-4991-b23c-8adc4d0d2536
```

**2.** `f998c173-...`
📁 ...
📅 ...
💬 ...
📌 ...
```bash
cd ... && claude -r ...
```
````

最後に「どれか再開する? あるいはクエリ絞り込む?」と聞く。

## 重要な注意

- **`claude -r <id>` は元の cwd で実行する必要がある**ため、出力には `cd <cwd> && claude -r <id>` の形で出す
- resume コマンドは必ず単独の fenced code block にする。`/copy` でコピー単位として認識されるため、複数セッションのコマンドを 1 つの code block にまとめない
- code block は **top-level**（左端揃え、インデントなし）で出す。`/copy` はリスト内にネストされた code block を拾えないため、メタ情報も `-` の箇条書きにせず plain text の行で並べる
- **勝手に `claude -r` を実行しない**。現セッションを抜ける操作はユーザーに任せる
- subagent セッションは検索対象外。メインのみ
- ヒット 0 件: クエリを言い換える or 緩める。それでも 0 件なら「見つからない」と素直に返す
- ヒット 50+ 件: クエリ絞り込みをユーザーに提案する
- セッションファイルが巨大（数 MB 超）な場合は Read を offset/limit で部分的に読む

## 設計判断

- なぜ embedding ベースのベクトル検索ではないか: 数千セッション規模なら grep + Claude による再ランクで十分実用的、かつインデックス更新・埋め込みコスト・staleness の問題が無い。grep の取りこぼしが頻発するようになったら embedding を後付けで足せばよい。
- なぜ TUI ではなくスキルか: Claude Code 自身に検索させれば「中身を読んで判断する」部分が無料で手に入る。外部 CLI を作ると同じ判断ロジックを再実装することになる。
