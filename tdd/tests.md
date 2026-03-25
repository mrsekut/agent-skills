# 良いテストと悪いテスト

## 良いテスト

**インテグレーションスタイル**: 内部パーツのモックではなく、実際のインターフェースを通してテストする。

```typescript
// 良い: 観察可能な振る舞いをテスト
test("user can checkout with valid cart", async () => {
	const cart = createCart();
	cart.add(product);
	const result = await checkout(cart, paymentMethod);
	expect(result.status).toBe("confirmed");
});
```

特徴：

- ユーザー/呼び出し元が関心を持つ振る舞いをテスト
- パブリックAPIのみを使用
- 内部リファクタリングに耐える
- HOW（どうやるか）ではなくWHAT（何をするか）を記述
- テストごとに1つの論理的アサーション

## 悪いテスト

**実装詳細テスト**: 内部構造に結合している。

```typescript
// 悪い: 実装の詳細をテストしている
test("checkout calls paymentService.process", async () => {
	const mockPayment = jest.mock(paymentService);
	await checkout(cart, payment);
	expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

危険信号：

- 内部の協調オブジェクトをモックしている
- プライベートメソッドをテストしている
- 呼び出し回数/順序をアサートしている
- 振る舞いの変更なしにリファクタリングするとテストが壊れる
- テスト名がWHAT（何をするか）ではなくHOW（どうやるか）を記述している
- インターフェースではなく外部手段を通じて検証している

```typescript
// 悪い: インターフェースをバイパスして検証している
test("createUser saves to database", async () => {
	await createUser({ name: "Alice" });
	const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
	expect(row).toBeDefined();
});

// 良い: インターフェースを通じて検証している
test("createUser makes user retrievable", async () => {
	const user = await createUser({ name: "Alice" });
	const retrieved = await getUser(user.id);
	expect(retrieved.name).toBe("Alice");
});
```
