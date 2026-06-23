#!/usr/bin/env python3
"""Build source chunks and annotation prompts for a course assistant dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SUPPORTED_SUFFIXES = {".pdf", ".pptx", ".txt", ".md"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", nargs="+", required=True, help="Course files or folders.")
    parser.add_argument("--out", default="data/course_assistant_annotation_prompts.jsonl")
    parser.add_argument("--mode", choices=["chunks", "sft_prompts", "dpo_prompts"], default="sft_prompts")
    parser.add_argument("--max-chars", type=int, default=1400)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--name-regex", default="", help="Optional regex filter applied to each file name.")
    args = parser.parse_args()

    name_pattern = re.compile(args.name_regex) if args.name_regex else None
    files = list(iter_files([Path(item).expanduser() for item in args.source], name_pattern=name_pattern))
    if not files:
        print("No supported files found. Supported suffixes: .pdf, .pptx, .txt, .md", file=sys.stderr)
        return 2

    rows = []
    for file_path in files:
        for section in extract_file(file_path):
            for chunk_index, chunk in enumerate(chunk_text(section["text"], max_chars=args.max_chars), start=1):
                chunk_row = {
                    "id": build_id(file_path, section["locator"], chunk_index),
                    "source_file": str(file_path.resolve()),
                    "source_name": file_path.name,
                    "locator": section["locator"],
                    "text": chunk,
                }
                rows.append(convert_row(args.mode, chunk_row))
                if args.limit and len(rows) >= args.limit:
                    break
            if args.limit and len(rows) >= args.limit:
                break
        if args.limit and len(rows) >= args.limit:
            break

    write_jsonl(args.out, rows)
    print(f"Wrote {len(rows)} rows to {args.out}")
    return 0


def iter_files(paths: list[Path], name_pattern: re.Pattern[str] | None = None):
    seen = set()
    for path in paths:
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES and matches_name(path, name_pattern):
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield resolved
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in SUPPORTED_SUFFIXES and matches_name(child, name_pattern):
                    resolved = child.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        yield resolved


def matches_name(path: Path, name_pattern: re.Pattern[str] | None) -> bool:
    return name_pattern is None or bool(name_pattern.search(path.name))


def extract_file(file_path: Path) -> list[dict[str, str]]:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(file_path)
    if suffix == ".pptx":
        return extract_pptx(file_path)
    return [{"locator": "file", "text": file_path.read_text(encoding="utf-8", errors="ignore")}]


def extract_pdf(file_path: Path) -> list[dict[str, str]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install PDF support with: pip install -r requirements/course_tune.txt") from exc

    reader = PdfReader(str(file_path))
    rows = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            rows.append({"locator": f"page:{page_number}", "text": text})
    return rows


def extract_pptx(file_path: Path) -> list[dict[str, str]]:
    try:
        from pptx import Presentation
    except ImportError as exc:
        raise RuntimeError("Install PPTX support with: pip install -r requirements/course_tune.txt") from exc

    presentation = Presentation(str(file_path))
    rows = []
    for slide_number, slide in enumerate(presentation.slides, start=1):
        parts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                parts.append(shape.text)
        if parts:
            rows.append({"locator": f"slide:{slide_number}", "text": "\n".join(parts)})
    return rows


def convert_row(mode: str, chunk: dict[str, str]) -> dict[str, str]:
    if mode == "chunks":
        return chunk

    if mode == "sft_prompts":
        prompt = f"""你是数据标注员。请根据下面课程资料生成 3 条中文 SFT 训练样本。

要求：
1. 只能使用资料中的信息，不要补充外部知识。
2. 问题要覆盖定义、比较、机制或应用。
3. 输出 JSONL，每行包含 instruction, input, output, system, source_files。

来源：{chunk["source_name"]} {chunk["locator"]}

资料：
{chunk["text"]}"""
    else:
        prompt = f"""你是偏好数据标注员。请根据下面课程资料生成 2 条中文 DPO 偏好样本。

要求：
1. chosen 必须准确、清楚、忠于资料。
2. rejected 应包含常见错误、遗漏关键条件或答非所问。
3. 输出 JSONL，每行包含 instruction, input, chosen, rejected, system, source_files。

来源：{chunk["source_name"]} {chunk["locator"]}

资料：
{chunk["text"]}"""

    return {
        "id": f"{mode}_{chunk['id']}",
        "source_file": chunk["source_file"],
        "locator": chunk["locator"],
        "prompt": prompt,
    }


def chunk_text(text: str, max_chars: int) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]
    chunks = []
    start = 0
    while start < len(normalized):
        chunk = normalized[start : start + max_chars].strip()
        if chunk:
            chunks.append(chunk)
        start += max_chars
    return chunks


def normalize_text(text: str) -> str:
    lines = []
    for line in text.replace("\x00", " ").splitlines():
        compact = re.sub(r"\s+", " ", line).strip()
        if compact:
            lines.append(compact)
    return "\n".join(lines)


def build_id(file_path: Path, locator: str, chunk_index: int) -> str:
    raw = f"{file_path.resolve()}::{locator}::{chunk_index}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def write_jsonl(path: str, rows: list[dict[str, str]]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
