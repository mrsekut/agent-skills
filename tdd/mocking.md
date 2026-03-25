# モックを使うべきとき

**システム境界**でのみモックする：

- 外部API（決済、メール等）
- データベース（場合による - テスト用DBを推奨）
- 時刻/乱数
- ファイルシステム（場合による）

モックしない：

- 自分自身のクラス/モジュール
- 内部の協調オブジェクト
- 自分がコントロールできるもの全般

## モックしやすさのための設計

システム境界では、モックしやすいインターフェースを設計する：

**1. 依存性の注入を使う**

外部の依存関係を内部で生成するのではなく、外から渡す：

```typescript
// モックしやすい
function processPayment(order, paymentClient) {
	return paymentClient.charge(order.total);
}

// モックしにくい
function processPayment(order) {
	const client = new StripeClient(process.env.STRIPE_KEY);
	return client.charge(order.total);
}
```

**2. 汎用的なフェッチャーよりSDKスタイルのインターフェースを好む**

条件分岐を含む汎用的な関数ではなく、各外部操作ごとに個別の関数を作成する：

```typescript
// 良い: 各関数が独立してモック可能
const api = {
	getUser: (id) => fetch(`/users/${id}`),
	getOrders: (userId) => fetch(`/users/${userId}/orders`),
	createOrder: (data) => fetch("/orders", { method: "POST", body: data }),
};

// 悪い: モックに条件分岐ロジックが必要になる
const api = {
	fetch: (endpoint, options) => fetch(endpoint, options),
};
```

SDKアプローチの利点：

- 各モックが特定の1つの形状を返す
- テストセットアップに条件分岐ロジックが不要
- テストがどのエンドポイントを実行しているか見やすい
- エンドポイントごとの型安全性
