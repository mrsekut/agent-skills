---
name: nixpkgs-register
description: nixpkgsに新しいパッケージを登録するPRを作成するワークフロー。「nixpkgsにパッケージを追加したい」「nixpkgsにPRを出したい」「nixpkgsに登録したい」「Nixパッケージを作りたい」「このツールをnixpkgsに入れたい」といった場面で使う。
---

# nixpkgs-register

nixpkgsリポジトリに新しいパッケージを追加するPRを出すための一連のワークフロー。

## 前提条件

- Nix がインストールされている
- GitHub アカウントがある
- `gh` CLI が認証済み

## ワークフロー概要

```
1. 対象パッケージの調査
2. nixpkgs の fork・clone
3. package.nix の作成
4. ビルド・テスト
5. メンテナー登録（初回のみ）
6. PR の作成
```

---

## Phase 1: 対象パッケージの調査

まずパッケージングに必要な情報を集める。

### 1-1: 既存パッケージの確認

nixpkgsに既に存在しないことを確認する。

```bash
nix search nixpkgs <パッケージ名>
```

GitHub issueやPRも検索して、誰かが既に作業中でないか確認する。

```bash
gh search prs --repo NixOS/nixpkgs "<パッケージ名>" --limit 10
gh search issues --repo NixOS/nixpkgs "<パッケージ名>" --limit 10
```

### 1-2: ソースコードの調査

パッケージングに必要な以下の情報を調べる。

- **ソースの場所**: GitHubリポジトリのURL、リリースタグの形式（`v1.0.0` 等）
- **ビルドシステム**: npm/pnpm/yarn、Cargo（Rust）、Go、Python、CMake、Meson等
- **ライセンス**: LICENSE ファイルの内容
- **依存関係**: ランタイム依存、ビルド時依存
- **成果物**: CLI バイナリか、ライブラリか、GUI アプリか
- **mainProgram**: 主要な実行ファイル名（パッケージ名と異なる場合がある）

### 1-3: ビルドシステムの選定

調査結果に基づき、使用するNixビルダーを決定する。

| ビルドシステム | Nix ビルダー                    | hash フィールド              |
| -------------- | ------------------------------- | ---------------------------- |
| npm            | `buildNpmPackage`               | `npmDepsHash`                |
| Cargo (Rust)   | `rustPlatform.buildRustPackage` | `cargoHash`                  |
| Go             | `buildGoModule`                 | `vendorHash`                 |
| Python (pip)   | `buildPythonPackage`            | なし（`dependencies`で指定） |
| CMake          | `stdenv.mkDerivation` + `cmake` | なし                         |
| Meson          | `stdenv.mkDerivation` + `meson` | なし                         |

類似パッケージのpackage.nixを参考にする。以下で検索できる:

```bash
# GitHub上でnixpkgsリポジトリ内を検索
gh api search/code -f q="buildNpmPackage filename:package.nix repo:NixOS/nixpkgs" --jq '.items[:5] | .[].path'
```

---

## Phase 2: nixpkgs の準備

### 2-1: Fork と Clone

初回のみ必要。既にfork済みならスキップ。

```bash
# fork（既にfork済みなら不要）
gh repo fork NixOS/nixpkgs --clone=false

# clone（shallow cloneで高速化）
git clone --depth=1 https://github.com/<ユーザー名>/nixpkgs.git
cd nixpkgs

# upstream設定
git remote add upstream https://github.com/NixOS/nixpkgs.git
```

注意: nixpkgsは非常に巨大なリポジトリ。`--depth=1` で shallow clone することを強く推奨する。

### 2-2: ブランチ作成

```bash
git fetch upstream master --depth=1
git checkout -b <パッケージ名>-init upstream/master
```

ブランチ名はわかりやすければ何でもよい。`<パッケージ名>-init` が一般的。

---

## Phase 3: package.nix の作成

### 3-1: ディレクトリの作成

`pkgs/by-name/` 以下に、パッケージ名の先頭2文字のディレクトリを作る。

```bash
# 例: "vite-plus" の場合
mkdir -p pkgs/by-name/vi/vite-plus
```

ルール:

- 先頭2文字は小文字にする
- パッケージ名はpnameと一致させる
- ハイフンをスネークケースやキャメルケースに変換しない

### 3-2: package.nix の作成

`pkgs/by-name/<2文字>/<パッケージ名>/package.nix` を作成する。

ビルドシステムに応じたテンプレートを使う。以下に主要なテンプレートを示す。

#### テンプレート: buildNpmPackage

```nix
{
  lib,
  buildNpmPackage,
  fetchFromGitHub,
  versionCheckHook,
  nix-update-script,
}:

buildNpmPackage (finalAttrs: {
  pname = "<パッケージ名>";
  version = "<バージョン>";

  src = fetchFromGitHub {
    owner = "<GitHubオーナー>";
    repo = "<リポジトリ名>";
    tag = "v${finalAttrs.version}";
    hash = "";  # 初回ビルド時にエラーで正しい値が表示される
  };

  npmDepsHash = "";  # prefetch-npm-deps package-lock.json で取得

  # 必要に応じて以下を追加
  # dontNpmBuild = true;  # ビルドステップが不要な場合
  # makeCacheWritable = true;  # キャッシュ書き込みが必要な場合
  # npmPackFlags = [ "--ignore-scripts" ];  # postinstall等をスキップ

  doInstallCheck = true;
  nativeInstallCheckInputs = [ versionCheckHook ];

  passthru.updateScript = nix-update-script { };

  meta = {
    description = "<説明文>";
    homepage = "<ホームページURL>";
    changelog = "https://github.com/<owner>/<repo>/releases/tag/v${finalAttrs.version}";
    license = lib.licenses.<ライセンス>;
    maintainers = with lib.maintainers; [ <GitHubユーザー名> ];
    mainProgram = "<実行ファイル名>";
  };
})
```

#### テンプレート: buildRustPackage

```nix
{
  lib,
  fetchFromGitHub,
  nix-update-script,
  rustPlatform,
  versionCheckHook,
}:

rustPlatform.buildRustPackage (finalAttrs: {
  pname = "<パッケージ名>";
  version = "<バージョン>";

  src = fetchFromGitHub {
    owner = "<GitHubオーナー>";
    repo = "<リポジトリ名>";
    tag = "v${finalAttrs.version}";
    hash = "";
  };

  cargoHash = "";  # 初回ビルド時にエラーで正しい値が表示される

  doInstallCheck = true;
  nativeInstallCheckInputs = [ versionCheckHook ];

  passthru.updateScript = nix-update-script { };

  meta = {
    description = "<説明文>";
    homepage = "<ホームページURL>";
    changelog = "https://github.com/<owner>/<repo>/releases/tag/v${finalAttrs.version}";
    license = lib.licenses.<ライセンス>;
    platforms = with lib.platforms; linux ++ darwin;
    maintainers = with lib.maintainers; [ <GitHubユーザー名> ];
    mainProgram = "<実行ファイル名>";
  };
})
```

#### テンプレート: buildGoModule

```nix
{
  lib,
  buildGoModule,
  fetchFromGitHub,
  nix-update-script,
  versionCheckHook,
}:

buildGoModule (finalAttrs: {
  pname = "<パッケージ名>";
  version = "<バージョン>";

  src = fetchFromGitHub {
    owner = "<GitHubオーナー>";
    repo = "<リポジトリ名>";
    tag = "v${finalAttrs.version}";
    hash = "";
  };

  vendorHash = "";  # 初回ビルド時にエラーで正しい値が表示される

  doInstallCheck = true;
  nativeInstallCheckInputs = [ versionCheckHook ];

  passthru.updateScript = nix-update-script { };

  meta = {
    description = "<説明文>";
    homepage = "<ホームページURL>";
    license = lib.licenses.<ライセンス>;
    maintainers = with lib.maintainers; [ <GitHubユーザー名> ];
    mainProgram = "<実行ファイル名>";
  };
})
```

### 3-3: meta セクションのルール

`meta` は package.nix の**最後**に配置する。以下のフィールドに注意:

- **description**: 1文で書く。大文字始まり。冠詞（A/An/The）で始めない。パッケージ名自体を含めない。末尾にピリオドは不要
  - 良い例: `"Ergonomic keyboard layout generator"`
  - 悪い例: `"A tool called Ergogen for generating keyboard layouts."`
- **license**: 上流のライセンスと一致させる。`lib.licenses.mit`, `lib.licenses.asl20`, `lib.licenses.gpl3Only` 等
- **maintainers**: 自分のGitHubユーザー名を入れる（Phase 5でmaintainer-list.nixに登録が必要）
- **mainProgram**: バイナリ名がpnameと異なる場合は必ず指定する
- **platforms**: 特定のプラットフォームでしか動かない場合に指定。省略するとすべてのプラットフォームが対象になる

---

## Phase 4: ビルドとテスト

### 4-1: hash の取得

初回は hash を空文字 `""` または `lib.fakeHash` にしてビルドし、エラーメッセージから正しい hash をコピーする。

```bash
# nixpkgsリポジトリのルートで実行
nix-build -A <パッケージ名>
```

エラーメッセージに `got: sha256-XXXX...` と表示されるので、その値を package.nix の該当フィールドに貼り付ける。

hash を埋める順序:

1. まず `src` の `hash` → ビルドエラーから取得して埋める
2. 次に依存関係の hash（`npmDepsHash`, `cargoHash`, `vendorHash`）→ 再度ビルドしてエラーから取得

npmの場合は `prefetch-npm-deps` も使える:

```bash
nix-shell -p prefetch-npm-deps --run "prefetch-npm-deps package-lock.json"
```

### 4-2: ビルドの確認

hashを埋めたら再度ビルドする。

```bash
nix-build -A <パッケージ名>
```

成功すると `./result` シンボリックリンクが作られる。

### 4-3: 動作テスト

ビルド成果物が正しく動くか確認する。

```bash
# バイナリの確認
ls ./result/bin/

# バージョン表示等で動作確認
./result/bin/<実行ファイル名> --version
./result/bin/<実行ファイル名> --help
```

### 4-4: フォーマット

nixpkgsはフォーマッターの使用を推奨している。

```bash
# nixfmt で整形
nix-shell -p nixfmt-rfc-style --run "nixfmt pkgs/by-name/<2文字>/<パッケージ名>/package.nix"
```

---

## Phase 5: メンテナー登録（初回コントリビューションのみ）

nixpkgsへの初回コントリビューションでは、自分をメンテナーリストに追加する必要がある。

### 5-1: maintainer-list.nix の編集

`maintainers/maintainer-list.nix` を編集し、アルファベット順の正しい位置に自分のエントリを追加する。

```nix
<GitHubユーザー名> = {
  email = "<メールアドレス>";
  github = "<GitHubユーザー名>";
  githubId = <GitHubユーザーID（数値）>;
  name = "<表示名>";
};
```

GitHubのユーザーIDは以下で確認できる:

```bash
gh api users/<GitHubユーザー名> --jq '.id'
```

### 5-2: コミットの分離

メンテナー登録は package.nix とは**別のコミット**にする。

```bash
# メンテナー追加を先にコミット
git add maintainers/maintainer-list.nix
git commit -m "maintainers: add <GitHubユーザー名>"
```

---

## Phase 6: コミットと PR 作成

### 6-1: コミット

package.nix のコミットメッセージは `<パッケージ名>: init at <バージョン>` という形式にする。

```bash
git add pkgs/by-name/<2文字>/<パッケージ名>/package.nix
git commit -m "<パッケージ名>: init at <バージョン>"
```

### 6-2: Push

```bash
git push origin <ブランチ名>
```

### 6-3: PR の作成

PRのタイトルも `<パッケージ名>: init at <バージョン>` とする。この形式が重要で、CIの自動ビルドのトリガーになる。

```bash
gh pr create --repo NixOS/nixpkgs \
  --title "<パッケージ名>: init at <バージョン>" \
  --body "$(cat <<'EOF'
<パッケージの簡単な説明>

homepage: <ホームページURL>

## Things done

- Built on platform(s)
  - [ ] x86_64-linux
  - [ ] aarch64-linux
  - [ ] x86_64-darwin
  - [x] aarch64-darwin
- For non-Linux: Is sandboxing enabled in `nix.conf`? (See [Nix manual](https://nixos.org/manual/nix/stable/command-ref/conf-file.html))
  - [ ] `sandbox = relaxed`
  - [ ] `sandbox = true`
- [ ] Tested, as applicable:
  - [NixOS test(s)](https://nixos.org/manual/nixos/unstable/index.html#sec-nixos-tests) (look inside [nixos/tests](https://github.com/NixOS/nixpkgs/blob/master/nixos/tests))
  - and/or [package tests](https://github.com/NixOS/nixpkgs/blob/master/pkgs/README.md#package-tests)
  - or, for functions and "core" functionality, tests in [lib/tests](https://github.com/NixOS/nixpkgs/blob/master/lib/tests) or [pkgs/test](https://github.com/NixOS/nixpkgs/blob/master/pkgs/test)
  - made sure NixOS tests are [linked](https://github.com/NixOS/nixpkgs/blob/master/pkgs/README.md#linking-nixos-module-tests-to-a-package) to the relevant packages
- [ ] Tested compilation of all packages that depend on this change using `nix-shell -p nixpkgs-review --run "nixpkgs-review rev HEAD"`. Note: all changes have to be committed, also see [nixpkgs-review usage](https://github.com/Mic92/nixpkgs-review#usage)
- [x] Tested basic functionality of all binary files (usually in `./result/bin/`)
- [x] Fits [CONTRIBUTING.md](https://github.com/NixOS/nixpkgs/blob/master/CONTRIBUTING.md).
EOF
)"
```

ビルドを確認したプラットフォームのチェックボックスを `[x]` に変更すること。

---

## トラブルシューティング

### hash mismatch

`hash` や `npmDepsHash` が合わないエラーが出た場合、エラーメッセージの `got:` の値をそのままコピーして貼り付ける。

### npmDepsHash が取れない

`package-lock.json` がリポジトリに含まれていない場合、ビルド前に生成する必要がある。`npmDeps` の代わりに `importNpmLock` を使う方法もある。詳しくは [nixpkgs JavaScript docs](https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/javascript.section.md) を参照。

### ビルドは通るがバイナリが動かない

ランタイム依存が不足している可能性がある。`nativeBuildInputs`（ビルド時のみ）と `buildInputs`（ランタイム）を確認する。共有ライブラリが必要な場合は `autoPatchelfHook` の使用を検討する。

### パッケージ名が数字で始まる

属性名にアンダースコアのプレフィックスを付ける（例: `0ad` → ディレクトリ名は `_0ad`）。ただし `pname` はそのまま `"0ad"` とする。

---

## 参考リンク

- [nixpkgs CONTRIBUTING.md](https://github.com/NixOS/nixpkgs/blob/master/CONTRIBUTING.md)
- [pkgs/README.md](https://github.com/NixOS/nixpkgs/blob/master/pkgs/README.md)
- [JavaScript/Node.js パッケージング](https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/javascript.section.md)
- [Flox: Contributing to nixpkgs ガイド](https://flox.dev/blog/contributing-to-nixpkgs/)
- [Contributing to nixpkgs - Basic Contributions](https://raghavsood.com/blog/2024/05/20/contributing-to-nixpkgs-basics/)
