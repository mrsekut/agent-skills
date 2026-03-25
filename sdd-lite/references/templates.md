# ドキュメントテンプレート

## 1-context

```markdown
# コンテキスト: {タスク名}

## 技術スタック

- Framework:
- Language:
- Key libraries:

## 関連する既存コード

- `path/to/file.ts`: 関連性の説明
- `path/to/component/`: 関連性の説明

## プロジェクト規約

- 命名規則:
- ディレクトリ構成:
- 使用パターン:

## 制約事項

-
```

## 2-prototyping-learnings

```markdown
# プロトタイピングの学び: {タスク名}

## うまくいったこと

-

## 違和感があったこと

-

## 発見された要件

プロトタイピングを通じて明らかになった要件や制約:

-

## UXに関する知見

設計に影響を与えるべき知見:

-

## メモ

追加の観察事項:

-
```

## 3-requirements

```markdown
# 要件: {タスク名}

## ユーザーストーリー

[ユーザー種別]として、[利益]を得るために、[操作]をしたい。

## 受け入れ基準

- [ ] 基準 1
- [ ] 基準 2
- [ ] 基準 3

## スコープ

### スコープ内

- 項目 1
- 項目 2

### スコープ外

- 項目 1
- 項目 2
```

## 4-design

````markdown
# 設計: {タスク名}

## ドメインモデル

コアとなる型定義のみ。ユーティリティ型や内部の詳細は含まない。

```typescript
interface Article {
	id: ArticleId;
	title: string;
	content: Content;
	author: UserId;
}
```

## 機能の境界

| 機能    | 責務                     | 依存先        |
| ------- | ----------------------- | ------------- |
| article | 記事のCRUD操作           | user, storage |
| user    | ユーザー管理              | -             |
| storage | 永続化レイヤー            | -             |

## ディレクトリ構成（機能単位のパッケージング）

機能レベルの構成のみ。各機能内の詳細なファイル構成は含まない。

```
src/
├── features/
│   ├── article/
│   ├── user/
│   └── storage/
└── shared/
    └── utils/
```

## メインフロー

主要な処理ステップとデータ変換。

1. `validateInput`: RawInput → ValidatedInput
2. `fetchArticle`: ArticleId → Article
3. `transformForDisplay`: Article → ArticleViewModel
4. `render`: ArticleViewModel → ReactElement

## レイヤー構成

各ロジックの配置先。できる限りコア（最も内側のレイヤー）に寄せる。

まずプロジェクトのレイヤー階層を特定し、次に各ロジックを割り当てる。

レイヤーの例（React）:

```
Core → State → Hooks → Components
```

レイヤーの例（バックエンド）:

```
Domain → Application → Controller → Handler
```

| ロジック       | レイヤー       | 理由                            |
| ------------- | ------------- | ------------------------------ |
| validateInput | Core          | 純粋関数、依存なし               |
| fetchArticle  | Core          | 注入可能、テスト可能              |
| ...           | （外側のレイヤー） | フレームワーク/インフラが必要      |
````

## 5-implementation-plan

```markdown
# 実装計画 {N}: {PRタイトル}

## 概要

このPRで達成する内容の簡潔な説明。

## 依存関係

- 前提: 5-implementation-plan-{X}（ある場合）
- ブロック: 5-implementation-plan-{Y}（ある場合）
- 並行: 5-implementation-plan-{Z} と並行して実行可能

## タスク

### セットアップ

- [ ] タスク 1
- [ ] タスク 2

### コア実装

- [ ] タスク 3
- [ ] タスク 4

### レビュー可能性

このPRのレビュー方法:

- [ ] テストが期待される振る舞いを示している
- [ ] （または）型が明確なインターフェースを定義している
- [ ] （または）動作するUIで手動検証が可能

### 検証

- [ ] tsc が通る
- [ ] lint が通る
- [ ] tests が通る

## 推奨コミット

1. `feat: add base structure for feature`
2. `feat: implement core logic`
3. `test: add tests for feature`
```
