---
name: nix-comma
description: Nixの`,`（comma）コマンドで、ローカル未インストールのツールをワンショット実行する。「commaを使って」「カンマを使って」「, で実行して」「`, yt-dlp` みたいに」と言われたら、`nix-shell -p` ではなくこのスキルに従って `,` を使う。任意のCLI（yt-dlp, ffmpeg, jq, imagemagick等）が必要なときに第一選択として使うこと。
---

# nix-comma

[nix-community/comma](https://github.com/nix-community/comma) は、nixpkgs にあるツールを **インストールせずに** その場で1回だけ実行するためのコマンド。ユーザーのマシンには既に `,` が入っている前提でよい。

## 基本パターン

```bash
, <パッケージ名> [引数...]
```

例:

```bash
, yt-dlp https://example.com/video
, ffmpeg -i in.mp4 out.webm
, jq '.foo' data.json
```

`,` の後ろは普通にそのコマンドを叩くのと同じ感覚で書ける。`--run "..."` のような引用は不要。

## 使いどころ

- ツールがローカルに無くても実行したいとき
- 1回しか使わないので恒久インストールしたくないとき
- スキルやスクリプトの中で外部ツールに依存するとき

`which <tool>` で見つからなくても、`, <tool>` でそのまま実行を試してよい。

## パッケージ名がコマンド名と違うとき

`,` は引数のコマンド名から nixpkgs の attribute を逆引きする。コマンド名と attribute が一致しないツール（例: `convert` → `imagemagick`）は `, -p imagemagick convert ...` のように `-p` で attribute を明示する。

詳細は https://github.com/nix-community/comma を参照。
