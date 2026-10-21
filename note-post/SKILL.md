---
name: note-post
description: |
  Markdown の記事を playwriter でユーザーの Chrome を操作して note.com に下書き保存・公開する。
  「noteに上げて」「noteに下書き保存して」「この記事をnoteに投稿して」と言われたときに使う。
  ログイン済みの普段の Chrome を使うので、認証ファイルや MCP は不要。
---

# note に投稿する

playwriter でユーザーの Chrome（note.com にログイン済み）を操作し、エディタに直接入力する。
操作手順は [Go-555/note-post-mcp](https://github.com/Go-555/note-post-mcp) の実装（`src/index.ts`）から抜き出したもの。note の UI が変わったらセレクタが壊れるので、失敗したらスクリーンショットを撮って今の DOM に合わせる。

## 原則

- **既定は下書き保存**。公開はユーザーが「公開して」と明示したときだけ。公開ボタンを押す直前にもう一度確認する
- 入力が終わったら毎回スクリーンショットを撮って、崩れていないか自分で確認する
- ユーザーのクリップボードを上書きしない（`navigator.clipboard` は使わず、合成 paste イベントで入れる）

## 手順

### 0. playwriter の準備

playwriter スキルを読み込み、`playwriter skill` で全文ドキュメントを読んでから始める。

- Chrome のプロファイルが複数あるので `session new --browser <key>` で選ぶ。note にログインしているのは個人プロファイル（`k.cloudspider@gmail.com`）
- 既存記事への追記なら、ユーザーが開いている編集タブ（`https://editor.note.com/notes/<id>/edit/`）を `context.pages()` から URL 完全一致で拾って使う。新しいタブは開かない

### 1. Markdown を分解する

- タイトル: front matter の `title:`、なければ最初の `# ` 行
- タグ: front matter の `tags:`（`[a, b]` 形式か `- a` 形式）
- 本文: 上記を除いた残り
- サムネイル: ユーザーが指定したときだけ

### 2. エディタを開いてタイトルを入れる

```js
state.page = await context.newPage();
await state.page.goto('https://editor.note.com/new', { waitUntil: 'domcontentloaded' });
await state.page.locator('textarea[placeholder*="タイトル"]').waitFor();
await state.page.locator('textarea[placeholder*="タイトル"]').fill(TITLE);
```

### 3. 本文を入れる

本文欄は `div[contenteditable="true"][role="textbox"]`（ProseMirror）。

**方法A（まず試す）: HTML を paste イベントで一括投入**（`h2`・`p`・`ul`・`blockquote` は 2026-10 に動作確認済み。`blockquote` は note の引用 `figure` に変換される）

本文 Markdown を HTML に変換し（見出しは `h2`/`h3`、コードは `pre><code`）、合成 paste イベントで流し込む。

```js
const box = state.page.locator('div[contenteditable="true"][role="textbox"]').first();
await box.click();
await box.evaluate((el, { html, text }) => {
  const dt = new DataTransfer();
  dt.setData('text/html', html);
  dt.setData('text/plain', text);
  el.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
}, { html: HTML, text: MARKDOWN });
```

既存記事の途中に足すときは、挿入位置の要素（空の `h2` など）を `click` → 見出しを `keyboard.type` → `End` → `Enter` で段落に移ってから paste する。入れ終わったら本文欄の子要素の `tagName` と `textContent` を出して構造を確かめる。

スクリーンショットで見出し・リスト・コードブロック・リンクが崩れていないか確認する。崩れていたら全消し（`Meta+a` → `Backspace`）して方法Bへ。

**方法B: 1行ずつタイプする（MCP と同じやり方）**

note のエディタは Markdown ショートカットに反応するので、`keyboard.type(line)` → `Enter` を繰り返す。ただし次の癖がある。

- **リスト・引用の継続行は記号を外す**: `- a` を打って Enter すると次行も自動でリストになる。2行目以降に `- ` を付けると二重になるので、直前がリスト（`- ` / `1. `）なら先頭記号を削ってから打つ。引用 `> ` も同じ
- **コードブロックはタイプしない**: ` ``` ` から ` ``` ` までを1塊にして、方法Aと同じ paste イベント（`text/plain` のみ）で入れる
- **URL だけの行はリンクカードになる**: タイプ後に Enter し、展開を ~1.2 秒待ってから `ArrowDown` でカードの外に出る
- **`---` の直後の空行は飛ばす**（余計な空段落ができる）

### 4. 本文中の画像（ローカルパスのものだけ）

画像の位置で改行し、ファイルを `File` にして paste イベントで入れる（2026-10 に動作確認済み。note の `assets.st-note.com` にアップロードされ `figure` になる）。アップロードに数秒かかるので待つ。

本文を方法Aで入れるときは、画像の位置に `<p>__IMAGE__</p>` のような目印を置いておき、後でその段落を選択して消してから paste すると位置がずれない。paste 後に直前に空段落が残るので、それも消す。

Cosense の gyazo 画像は `https://i.gyazo.com/<id>.png` を curl で落としてから使う。

```js
await box.evaluate(async (el, { base64, mime, name }) => {
  const blob = await (await fetch(`data:${mime};base64,${base64}`)).blob();
  const dt = new DataTransfer();
  dt.items.add(new File([blob], name, { type: mime }));
  el.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
}, { base64, mime, name });
```

base64 はローカルで `base64 -i <file>` して渡す。

### 5. サムネイル（指定されたときだけ）

1. `button[aria-label="画像を追加"]` のうち一番上にあるもの（`boundingBox().y` が最小）をクリック
2. `button:has-text("画像をアップロード")` をクリックし、`filechooser` イベントで `setFiles(path)`。来なければ `input[type="file"]` に `setInputFiles`
3. トリミングダイアログ `div[role="dialog"]` の `button:has-text("保存")` が有効になるのを待って押す
4. `button[aria-label="画像を変更"]` が出れば反映済み

### 6. 下書き保存

`button:has-text("下書き保存")` を押し、`text=保存しました` を待つ。`state.page.url()` が記事の編集 URL なので、それをユーザーに返す。

### 7. 公開（ユーザーが明示したときだけ）

1. `button:has-text("公開に進む")` を押す → URL が `/publish` に変わる
2. タグ: `input[placeholder*="ハッシュタグ"]`（なければ `input[role="combobox"]`）に1つずつ `fill` → `Enter`
3. スクリーンショットを見せて最終確認を取る
4. `button:has-text("投稿する")` を押し、URL が `/publish` から外れるか `text=投稿しました` を待つ
5. 公開後の URL を返す
