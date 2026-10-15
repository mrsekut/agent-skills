#!/usr/bin/env python3
"""本ディレクトリを Cosense 投稿用に変換した一時コピーを作る。

usage: prepare.py <book_dir> <out_dir> [--tag ai-book]

- 各 md 内の `[text](chNN.md)` を、リンク先章の H1 を使った Cosense リンク `[<H1>]` に置換
- README.md の H1 直下にタグ行 `#<tag>` を挿入
- README.md から既存の `Cosense: ...` 行（逆参照用に追記したもの）を除く
元のディレクトリは変更しない。
"""
import argparse
import re
import shutil
from pathlib import Path

LINK = re.compile(r"\[([^\]]*)\]\(([^)#\s]+\.md)(#[^)]*)?\)")


def h1(path: Path) -> str | None:
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--tag", default="ai-book")
    args = ap.parse_args()

    src, out = Path(args.book_dir).resolve(), Path(args.out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    titles = {p.name: h1(p) for p in src.glob("*.md")}

    def to_cosense(m: re.Match) -> str:
        title = titles.get(Path(m.group(2)).name)
        return f"[{title}]" if title else m.group(0)

    for p in sorted(src.glob("*.md")):
        lines = LINK.sub(to_cosense, p.read_text()).splitlines()
        if p.name == "README.md":
            lines = [l for l in lines if not l.startswith("Cosense: ")]
            i = next((i for i, l in enumerate(lines) if l.startswith("# ")), -1)
            if args.tag:
                lines.insert(i + 1, f"#{args.tag}")
        (out / p.name).write_text("\n".join(lines) + "\n")
        print(f"{p.name}\t{titles[p.name]}")


if __name__ == "__main__":
    main()
