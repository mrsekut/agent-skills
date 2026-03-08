#!/usr/bin/env python3
"""
Parse an OCR JSON book file (Cosense export format) into clean chapter text files.

Usage:
    python parse_book.py <ocr_json_path> <output_dir>

This script:
1. Reads the OCR JSON (Cosense page format)
2. Extracts clean text from > prefixed lines
3. Detects chapter boundaries (distinguishing TOC from body headings)
4. Handles multi-line chapter headings common in OCR output
5. Outputs per-chapter markdown files and a structure JSON
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict


def extract_content_lines(page):
    """Extract clean text lines from a page, removing metadata."""
    content = []
    for line in page.get("lines", []):
        if line.startswith("> "):
            text = line[2:].strip()
            if text:
                content.append(text)
    return content


def is_header_footer(line):
    """Detect common headers/footers that should be filtered."""
    # Progress percentage like "7%", "50%"
    if re.match(r"^\d+%$", line):
        return True
    # Reading time indicator
    if re.match(r"^章を読み終えるまで[:：]\s*\d+分$", line):
        return True
    if line.startswith("読書の速さを測定中"):
        return True
    return False


def detect_running_header(lines_across_pages):
    """
    Detect the book's running header by finding the most frequently repeated
    short line (often the book title, truncated with ... or similar).

    Returns a set of running header patterns to filter.
    """
    from collections import Counter
    short_lines = []
    for line in lines_across_pages:
        stripped = line.strip()
        # Running headers tend to be book titles, truncated, appearing on many pages
        if len(stripped) < 60 and (
            stripped.endswith("...") or stripped.endswith("・・・")
            or stripped.endswith("..") or stripped.endswith("･")
            or stripped.endswith("・・") or stripped.endswith("···")
            or stripped.endswith("…")
        ):
            short_lines.append(stripped)

    counter = Counter(short_lines)
    headers = set()
    for text, count in counter.items():
        # If a short truncated line appears on 10+ pages, it's a running header
        if count >= 10:
            headers.add(text)
    return headers


def detect_chapter_heading_single_line(line):
    """
    Detect if a single line is a chapter/part heading.
    Returns (chapter_type, chapter_number, chapter_title, confidence) or None.

    confidence:
      - "high": decorated heading like < 第1章 >, standalone はじめに, etc.
      - "medium": plain 第N章 at start of line
      - "low": could be a reference (第N章で...)
    """
    stripped = line.strip()

    # Skip lines that are clearly references to chapters within body text
    # e.g., "第3章で説明したように", "第2章の", "第5章で参照した"
    if re.match(r"^第\s*\d+\s*章[でのをにはがもと]", stripped):
        return None
    # Lines starting with chapter ref in mid-sentence context
    if re.match(r".*[、。].*第\s*\d+\s*章", stripped):
        return None

    # Skip long lines - headings are usually short
    if len(stripped) > 60:
        return None

    # Decorated heading: < 第N章 > or 〈第N章〉 — high confidence
    m = re.match(
        r"^[<＜〈«]\s*第\s*(\d+)\s*章\s*[>＞〉»]\s*(.*)$", stripped
    )
    if m:
        return ("chapter", int(m.group(1)), m.group(2).strip(), "high")

    # 第N部 with decorations
    m = re.match(
        r"^[<＜〈«]\s*第\s*(\d+)\s*部\s*[>＞〉»]\s*(.*)$", stripped
    )
    if m:
        return ("part", int(m.group(1)), m.group(2).strip(), "high")

    # Plain 第N章 — medium confidence if short, low if longer
    m = re.match(r"^第\s*(\d+)\s*章\s*(.*)$", stripped)
    if m:
        title = m.group(2).strip()
        confidence = "medium" if len(stripped) < 30 else "low"
        return ("chapter", int(m.group(1)), title, confidence)

    # Plain 第N部
    m = re.match(r"^第\s*(\d+)\s*部\s*(.*)$", stripped)
    if m:
        title = m.group(2).strip()
        confidence = "medium" if len(stripped) < 20 else "low"
        return ("part", int(m.group(1)), title, confidence)

    # N章 pattern (OCR sometimes drops 第) — only if very short
    m = re.match(r"^(\d+)\s*章\s+(.+)$", stripped)
    if m and len(stripped) < 30:
        return ("chapter", int(m.group(1)), m.group(2).strip(), "low")

    # はじめに — only if it's a short standalone line
    m = re.match(r"^はじめに\s*(.*)$", stripped)
    if m and len(stripped) < 40:
        title = m.group(1).strip()
        return ("intro", 0, f"はじめに {title}".strip(), "medium")

    # おわりに
    m = re.match(r"^おわりに\s*(.*)$", stripped)
    if m and len(stripped) < 40:
        title = m.group(1).strip()
        return ("outro", 999, f"おわりに {title}".strip(), "medium")

    # Chapter N (English)
    m = re.match(r"^Chapter\s+(\d+)\s*[:\.]?\s*(.*)$", stripped, re.IGNORECASE)
    if m and len(stripped) < 40:
        return ("chapter", int(m.group(1)), m.group(2).strip(), "medium")

    return None


def detect_multiline_chapter_heading(lines):
    """
    Detect multi-line chapter headings that OCR sometimes produces.

    Common patterns:
    1. "第" on one line, "N." on next, title on the line after
       (e.g., virtualization book: "第" / "2." / "起動してメッセージを")
    2. "第N" on one line, "章" on the next line
       (e.g., 22seiki book: "第2" / "章")
    3. ".N." (OCR artifact for 第N章) on one line, title on next
       (e.g., ".11." / "作成したハイパーバイザを")

    Returns list of (line_index, chapter_type, chapter_number, chapter_title, confidence)
    """
    results = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Pattern 1: "第" alone, then "N." on next line
        # Also handle "N%" which is an OCR artifact where the progress indicator
        # bleeds into the chapter number (e.g., "7." becomes "7%")
        if stripped == "第" and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            m = re.match(r"^(\d+)[.%]\s*$", next_stripped)
            if m:
                ch_num = int(m.group(1))
                # Gather title from subsequent short lines (max 2 lines, max 30 chars each)
                title_parts = []
                for j in range(i + 2, min(i + 4, len(lines))):
                    candidate = lines[j].strip()
                    if len(candidate) > 30 or not candidate:
                        break
                    if re.match(r"^\d+\.\d+", candidate):
                        break
                    title_parts.append(candidate)
                title = " ".join(title_parts) if title_parts else ""
                results.append((i, "chapter", ch_num, title, "high"))

        # Pattern 2a: "第N" alone, then "章" on next line
        m = re.match(r"^第\s*(\d+)$", stripped)
        if m and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            if next_stripped == "章":
                ch_num = int(m.group(1))
                title_parts = []
                for j in range(i + 2, min(i + 4, len(lines))):
                    candidate = lines[j].strip()
                    if len(candidate) > 30 or not candidate:
                        break
                    if re.match(r"^\d+\.\d+", candidate):
                        break
                    title_parts.append(candidate)
                title = " ".join(title_parts) if title_parts else ""
                results.append((i, "chapter", ch_num, title, "high"))

        # Pattern 2b: "第" alone, then "N" alone, then "章" alone (three-line split)
        if stripped == "第" and i + 2 < len(lines):
            next1 = lines[i + 1].strip()
            next2 = lines[i + 2].strip()
            m = re.match(r"^(\d+)$", next1)
            if m and next2 == "章":
                ch_num = int(m.group(1))
                title_parts = []
                for j in range(i + 3, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    if len(candidate) > 30 or not candidate:
                        break
                    if re.match(r"^\d+\.\d+", candidate):
                        break
                    title_parts.append(candidate)
                title = " ".join(title_parts) if title_parts else ""
                results.append((i, "chapter", ch_num, title, "high"))

        # Pattern 3: ".N." or "・N・" — OCR artifact for 第N章
        m = re.match(r"^[.・]\s*(\d+)\s*[.・]\s*$", stripped)
        if m:
            ch_num = int(m.group(1))
            title_parts = []
            for j in range(i + 1, min(i + 3, len(lines))):
                candidate = lines[j].strip()
                if len(candidate) > 30 or not candidate:
                    break
                if re.match(r"^\d+\.\d+", candidate):
                    break
                title_parts.append(candidate)
            title = " ".join(title_parts) if title_parts else ""
            results.append((i, "chapter", ch_num, title, "medium"))

    return results


def classify_pages(content_pages, total_pages):
    """
    Classify pages into TOC vs body based on their position and content density.

    TOC pages tend to:
    - Appear in the first ~15% of the book
    - Have multiple heading-like lines
    - Have short lines (just titles, not full paragraphs)
    - Have very few content lines (mostly just chapter titles)
    """
    toc_zone_end = max(int(total_pages * 0.15), 30)
    toc_pages = set()

    for p in content_pages:
        page_num = int(p["title"])
        if page_num > toc_zone_end:
            continue

        lines = extract_content_lines(p)
        clean_lines = [l for l in lines if not is_header_footer(l)]

        heading_count = sum(
            1 for l in clean_lines if detect_chapter_heading_single_line(l) is not None
        )

        # Also check for multi-line headings on this page
        multiline_headings = detect_multiline_chapter_heading(clean_lines)
        heading_count += len(multiline_headings)

        # Multiple headings on one page in the front of the book = TOC
        if heading_count >= 2:
            toc_pages.add(p["title"])
        # Single heading with very little other content = likely TOC entry page
        # (but only if the page has minimal content, not a chapter start)
        elif heading_count == 1 and len(clean_lines) <= 5 and page_num < toc_zone_end:
            # Additional check: if this page has a multiline heading with body text
            # after it, it's probably a real chapter start, not TOC
            if not multiline_headings:
                toc_pages.add(p["title"])

    return toc_pages


def parse_book(ocr_json_path):
    """Parse OCR JSON and return structured book data."""
    with open(ocr_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pages = data.get("pages", [])

    # Filter to numeric-titled pages (actual book pages)
    content_pages = [p for p in pages if re.match(r"^\d+$", p.get("title", ""))]
    total_pages = len(content_pages)

    # Detect running headers across all pages
    all_lines = []
    for p in content_pages:
        all_lines.extend(extract_content_lines(p))
    running_headers = detect_running_header(all_lines)

    if running_headers:
        print(f"Detected running headers: {running_headers}")

    # Classify TOC pages
    toc_pages = classify_pages(content_pages, total_pages)

    # Extract content with page references
    # We keep both raw and cleaned lines: raw for heading detection,
    # cleaned for the actual content stored in chapters
    book_content = []
    for p in content_pages:
        page_num = p["title"]
        raw_lines = extract_content_lines(p)
        # Remove running headers but keep header/footer lines for now
        # (multiline heading detection needs N% lines which look like footers)
        raw_no_header = [
            l for l in raw_lines
            if l.strip() not in running_headers
        ]
        clean_lines = [
            l for l in raw_lines
            if not is_header_footer(l) and l.strip() not in running_headers
        ]
        if clean_lines:
            book_content.append({
                "page": page_num,
                "lines": clean_lines,
                "raw_lines": raw_no_header,  # for heading detection
                "is_toc": page_num in toc_pages,
            })

    # First pass: collect all candidate headings from non-TOC body pages
    # Use raw_lines for multiline detection (needs N% lines),
    # use clean lines for single-line detection
    candidates = []
    for entry in book_content:
        if entry["is_toc"]:
            continue

        # Single-line heading detection (on cleaned lines)
        for line in entry["lines"]:
            heading = detect_chapter_heading_single_line(line)
            if heading:
                ch_type, ch_num, ch_title, confidence = heading
                candidates.append({
                    "page": entry["page"],
                    "type": ch_type,
                    "number": ch_num,
                    "title": ch_title,
                    "confidence": confidence,
                    "line": line,
                })

        # Multi-line heading detection (on raw lines to preserve N% etc.)
        multiline = detect_multiline_chapter_heading(entry["raw_lines"])
        for line_idx, ch_type, ch_num, ch_title, confidence in multiline:
            candidates.append({
                "page": entry["page"],
                "type": ch_type,
                "number": ch_num,
                "title": ch_title,
                "confidence": confidence,
                "line": entry["raw_lines"][line_idx],
            })

    # Build a map of page -> content size (chars on subsequent pages until next candidate)
    # This helps distinguish real chapter starts from TOC entries:
    # a real chapter start has substantial body text after it
    page_list = [e["page"] for e in book_content if not e["is_toc"]]
    page_char_counts = {}
    for e in book_content:
        if not e["is_toc"]:
            page_char_counts[e["page"]] = sum(len(l) for l in e["lines"])

    candidate_pages = set(c["page"] for c in candidates)

    def content_after_candidate(page):
        """Count chars from this page until the next candidate page."""
        try:
            idx = page_list.index(page)
        except ValueError:
            return 0
        total = 0
        for i in range(idx, min(idx + 20, len(page_list))):  # look ahead up to 20 pages
            p = page_list[i]
            if p != page and p in candidate_pages:
                break
            total += page_char_counts.get(p, 0)
        return total

    # Resolve duplicates: for same (type, number), prefer the candidate with
    # substantial body text following it (real chapter start vs TOC entry)
    grouped = defaultdict(list)
    for c in candidates:
        key = (c["type"], c["number"])
        grouped[key].append(c)

    chosen_headings = {}  # page -> heading info
    for key, group in grouped.items():
        if len(group) == 1:
            c = group[0]
            chosen_headings[c["page"]] = c
        else:
            # Score each candidate: high confidence + substantial content after it
            by_confidence = {"high": 3, "medium": 2, "low": 1}
            for c in group:
                c["_content_after"] = content_after_candidate(c["page"])

            best = max(group, key=lambda x: (
                # Strongly prefer candidates with substantial body text after them
                # (> 1000 chars = real chapter, < 500 chars = likely TOC entry)
                1 if x["_content_after"] > 1000 else 0,
                by_confidence.get(x["confidence"], 0),
                x["_content_after"],
            ))
            chosen_headings[best["page"]] = best

    # Second pass: build chapters using resolved headings
    chapters = []
    current_chapter = {
        "type": "front_matter",
        "number": -1,
        "title": "前付け",
        "start_page": "000",
        "pages": [],
    }

    for entry in book_content:
        if entry["is_toc"]:
            current_chapter["pages"].append(entry)
            continue

        page = entry["page"]
        if page in chosen_headings:
            heading = chosen_headings[page]

            # Save current chapter
            if current_chapter["pages"]:
                chapters.append(current_chapter)

            current_chapter = {
                "type": heading["type"],
                "number": heading["number"],
                "title": heading["title"] if heading["title"] else f"{heading['type']} {heading['number']}",
                "start_page": page,
                "pages": [entry],
            }
        else:
            current_chapter["pages"].append(entry)

    if current_chapter["pages"]:
        chapters.append(current_chapter)

    return chapters, toc_pages


def generate_chapter_slug(chapter, seen_slugs):
    """Generate a unique filename-safe slug for a chapter."""
    ch_type = chapter["type"]
    ch_num = chapter["number"]

    if ch_type == "front_matter":
        base = "ch00_front_matter"
    elif ch_type == "intro":
        base = "ch00_intro"
    elif ch_type == "outro":
        base = "ch99_outro"
    elif ch_type == "part":
        base = f"part{ch_num:02d}"
    else:
        base = f"ch{ch_num:02d}"

    # Ensure uniqueness
    slug = base
    counter = 2
    while slug in seen_slugs:
        slug = f"{base}_{counter}"
        counter += 1
    seen_slugs.add(slug)
    return slug


def write_chapter_file(chapter, slug, output_dir):
    """Write a chapter's content as a clean markdown file."""
    filepath = output_dir / f"{slug}.md"

    with open(filepath, "w", encoding="utf-8") as f:
        ch_type = chapter["type"]
        if ch_type == "part":
            f.write(f"# 第{chapter['number']}部 {chapter['title']}\n\n")
        elif ch_type == "chapter":
            f.write(f"# 第{chapter['number']}章 {chapter['title']}\n\n")
        elif ch_type in ("intro", "outro"):
            f.write(f"# {chapter['title']}\n\n")
        else:
            f.write(f"# {chapter['title']}\n\n")

        f.write(f"(pages {chapter['start_page']}-{chapter['pages'][-1]['page']})\n\n")

        for page_entry in chapter["pages"]:
            page_num = page_entry["page"]
            if page_entry.get("is_toc"):
                continue
            f.write(f"<!-- page {page_num} -->\n")
            for line in page_entry["lines"]:
                f.write(f"{line}\n")
            f.write("\n")

    return filepath


def main():
    if len(sys.argv) < 3:
        print("Usage: python parse_book.py <ocr_json_path> <output_dir>")
        sys.exit(1)

    ocr_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not ocr_path.exists():
        print(f"Error: {ocr_path} not found")
        sys.exit(1)

    chapters_dir = output_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    print(f"Parsing: {ocr_path.name}")

    chapters, toc_pages = parse_book(str(ocr_path))

    print(f"Found {len(chapters)} chapters/sections")
    if toc_pages:
        print(f"TOC pages (excluded from body): {sorted(toc_pages, key=int)}")

    # Quality check: warn about oversized chapters
    for chapter in chapters:
        char_count = sum(
            len(line)
            for pe in chapter["pages"]
            for line in pe["lines"]
            if not pe.get("is_toc")
        )
        if char_count > 100000:
            print(f"  WARNING: {chapter['title']} has {char_count:,} chars — "
                  f"chapter detection may have failed here")

    seen_slugs = set()
    structure = []
    for chapter in chapters:
        slug = generate_chapter_slug(chapter, seen_slugs)
        write_chapter_file(chapter, slug, chapters_dir)

        start = chapter["start_page"]
        end = chapter["pages"][-1]["page"]
        char_count = sum(
            len(line)
            for pe in chapter["pages"]
            for line in pe["lines"]
            if not pe.get("is_toc")
        )

        entry = {
            "slug": slug,
            "type": chapter["type"],
            "number": chapter["number"],
            "title": chapter["title"],
            "start_page": start,
            "end_page": end,
            "page_count": len(chapter["pages"]),
            "char_count": char_count,
            "file": f"chapters/{slug}.md",
        }
        structure.append(entry)
        print(f"  {slug}: {chapter['title']} (pages {start}-{end}, {char_count:,} chars)")

    structure_path = output_dir / "structure.json"
    with open(structure_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source_file": str(ocr_path),
                "total_chapters": len(structure),
                "chapters": structure,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\nStructure saved to: {structure_path}")
    print(f"Chapter files saved to: {chapters_dir}/")


if __name__ == "__main__":
    main()
