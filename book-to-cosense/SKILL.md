---
name: book-to-cosense
description: |
  mental-model-book などで書いた md の本（README.md + ch*.md）を md2cosense で Cosense に載せ、目次を章ページへのリンクにし、タグ（既定 #ai-book）を付け、md 側にも Cosense の URL を書き戻す。
  「この本を Cosense に載せて」「md2cosense して」「本を scrapbox に上げて」と言われたとき、または mental-model-book で本を書き終えたあとに使う。
---

# 本を Cosense に載せる

ユーザーは本を Cosense 上で読み、読んだページから消していく。そのため Cosense 側は「目次ページ → 各章ページ」をリンクでたどれる形にし、md 側には逆参照用に Cosense の URL を残す。

アップロード後に Cosense 上でリンクを直すのではなく、**変換済みの一時コピーを作ってから md2cosense にかける**。元の md は Cosense URL の追記以外では変更しない。

## 手順

### 1. 本ディレクトリと投稿先を確認する

- 本ディレクトリ: `README.md` と `ch*.md` を含むディレクトリ。直前に mental-model-book で書いた本ならそれを使う
- 投稿先 project: 必ずユーザに聞く
- タグ: 既定は `ai-book`。ユーザーが別のタグを指定したらそれに従う

### 2. 一時コピーを作る

```bash
python3 <skill_dir>/scripts/prepare.py <book_dir> <scratchpad>/book-to-cosense --tag ai-book
```

スクリプトがやること:

- `[text](chNN.md)` 形式の md リンクを、リンク先の章の H1 を使った `[<章のH1>]` に置換する（md2cosense はそのままだと `[ch01.md text]` という壊れたリンクにする）
- README の H1 の直下に `#ai-book` 行を挿入する
- 手順5で追記した `Cosense: ...` 行があれば除く（再投稿時用）
- `figures/` など md 以外のファイルも同じ相対パスでコピーする。本文の `![説明](figures/xxx.svg)` は md2cosense が投稿先 project にアップロードし、画像として埋め込む

出力（ファイル名とページタイトルの対応）はあとで使う。

### 3. dry-run で衝突を確認する

```bash
md2cosense <scratchpad>/book-to-cosense -p <project> --dry-run
```

- `[dry-run] https://...` の URL 末尾に `_2` などが付くページは、**同名ページが既に存在する**。再投稿か別の本との衝突かを判断できないので、該当ページを列挙して扱いをユーザーに聞く（既存を消してから投稿する / 衝突ページだけ除いて投稿する / やめる）
- リンク変換・タグ行が意図どおりかもここで見る
- 図があれば `🖼  figures/xxx.svg (will be uploaded)` と出る。`Image not found` で失敗したページは、本文の画像パスが間違っている

### 4. 投稿する

```bash
md2cosense <scratchpad>/book-to-cosense -p <project> -y
```

完了後、目次ページを `cosense browsePage` で1回読み、関連ページ一覧に各章が出ているかを確認する（反映遅れで出ないことはある。その場合はリンク表記と章タイトルが一致していれば良い）。

### 5. md 側に Cosense の URL を書き戻す

元の `README.md` の H1 の直下に1行追記する:

```
Cosense: https://scrapbox.io/<project>/<目次ページタイトル>
```

URL はタイトルの空白を `_` にしたものにする（`cosense browsePage` の Readable link と同じ形）。既に `Cosense:` 行があれば置き換える。

### 6. 報告する

- 目次ページの URL
- 投稿したページ数と、衝突でスキップ・置き換えたページ
