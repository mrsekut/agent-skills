---
name: skill-symlinker
description: agent-skillsリポジトリ内のスキルを~/.claude/skills/にsymlink化して即座に使えるようにする。「symlinkして」「symlink化して」「いったんsymlink」「このスキルをすぐ使いたい」「スキルをリンクして」「リンク貼って」と言われたらこのスキルを使う。スキル開発中にNixのビルドサイクルを待たずに素早くテストしたい場面で積極的に使うこと。
---

# Skill Symlinker

agent-skillsリポジトリで開発中のスキルを `~/.claude/skills/` にsymlinkして、Nixのrebuildを待たずに即座に使えるようにする。

## 背景

ユーザーはスキルをNix + dotfiles経由で `~/.claude/skills/` に配置している。通常フローは commit → push → dotfiles更新 → nix apply と手順が多い。開発・テスト中はリポジトリから直接symlinkを張ることで、このサイクルをスキップできる。

## パス

- リポジトリ: `agent-skills/`など基本呼び出しているカレントディレクトリになるはず
- スキル配置先: `~/.claude/skills/`

## 手順

1. ユーザーがsymlink化したいスキル名を指定する（指定がなければ、直近で作成・編集したスキルを推測して確認する）
2. 対象スキルのディレクトリがリポジトリ内に存在することを確認する
3. `~/.claude/skills/<スキル名>` に既存のsymlink（Nix storeへのリンク）があれば削除する
4. リポジトリ内のスキル**ディレクトリ**へのsymlinkを作成する:

   ```
   ln -sfn /absolute/path/to/<スキルディレクトリ> ~/.claude/skills/<スキル名>
   ```

   - **重要: リンク先は必ずSKILL.mdを含むディレクトリであること。SKILL.mdファイルを直接リンクしてはいけない。**
   - 既存の `~/.claude/skills/` 内のNix storeリンクを見ればわかるが、すべてディレクトリへのリンクになっている
   - agent-skills リポジトリ以外（例: 別リポジトリの `skills/` ディレクトリ内）にスキルがある場合も、そのディレクトリの絶対パスを使う

5. symlinkが正しく張られたことを `ls -la` で確認し、結果を報告する

## 複数スキルの一括処理

「全部symlinkして」と言われた場合は、リポジトリ内のSKILL.mdを持つ全ディレクトリを対象にする。

## Nixに戻す

「symlinkを元に戻して」と言われた場合は、Nixのrebuildが必要であることを伝える。手動で戻す場合は該当symlinkを削除してから `nix apply` 相当のコマンドを実行してもらう。
