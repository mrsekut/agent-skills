# テスタビリティのためのインターフェース設計

良いインターフェースはテストを自然にする：

1. **依存関係を受け取る、自ら生成しない**

   ```typescript
   // テストしやすい
   function processOrder(order, paymentGateway) {}

   // テストしにくい
   function processOrder(order) {
   	const gateway = new StripeGateway();
   }
   ```

2. **結果を返す、副作用を起こさない**

   ```typescript
   // テストしやすい
   function calculateDiscount(cart): Discount {}

   // テストしにくい
   function applyDiscount(cart): void {
   	cart.total -= discount;
   }
   ```

3. **小さな公開面積**
   - メソッドが少ない = 必要なテストが少ない
   - パラメータが少ない = テストのセットアップがシンプル
