"""
Chunker for the Northwind Robotics wiki corpus.

Strategy (structure-aware, not naive character splitting):
1. Parse each markdown file into sections by ## headers.
2. If a section fits within TARGET_TOKENS, keep it as one chunk.
3. If a section is longer, sub-split on paragraph boundaries with overlap,
   so we never cut mid-sentence and boundary content is not orphaned.
4. Every chunk carries full provenance metadata: source file, department,
   page title, section heading, chunk index within section.

Token counting: we use a word-count-based approximation
(1 word ~= 1.3 tokens for English), which is standard practice when an
exact tokenizer is not available or worth the dependency.
"""
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "chunks.jsonl"

TARGET_TOKENS = 700
MAX_TOKENS = 800
OVERLAP_TOKENS = 100
WORDS_TO_TOKENS = 1.3


def count_tokens(text: str) -> int:
    return int(len(text.split()) * WORDS_TO_TOKENS)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_file: str
    department: str
    page_title: str
    section_heading: str
    chunk_index_in_section: int
    token_count: int


def parse_frontmatter(text: str):
    lines = text.strip().split("\n")
    title = ""
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        lines = lines[1:]
    return title, "\n".join(lines)


def split_into_sections(body: str):
    pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(body))

    sections = []
    if not matches:
        sections.append(("Overview", body.strip()))
        return sections

    preamble = body[: matches[0].start()].strip()
    if preamble:
        sections.append(("Overview", preamble))

    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        if content:
            sections.append((heading, content))

    return sections


def split_long_section(text: str, max_tokens: int, overlap_tokens: int):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return [text]

    sub_chunks = []
    current_paras = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)
        if current_tokens + para_tokens > max_tokens and current_paras:
            sub_chunks.append("\n\n".join(current_paras))
            overlap_paras = []
            overlap_count = 0
            for p in reversed(current_paras):
                pt = count_tokens(p)
                if overlap_count + pt > overlap_tokens:
                    break
                overlap_paras.insert(0, p)
                overlap_count += pt
            current_paras = overlap_paras
            current_tokens = overlap_count

        current_paras.append(para)
        current_tokens += para_tokens

    if current_paras:
        sub_chunks.append("\n\n".join(current_paras))

    return sub_chunks


def merge_small_sections(sections, target_tokens: int, max_tokens: int):
    merged = []
    current_headings = []
    current_parts = []
    current_tokens = 0

    def flush():
        if current_parts:
            heading_label = " / ".join(current_headings)
            merged.append((heading_label, "\n\n".join(current_parts)))

    for heading, content in sections:
        content_tokens = count_tokens(content)

        if content_tokens > max_tokens:
            flush()
            current_headings, current_parts, current_tokens = [], [], 0
            merged.append((heading, content))
            continue

        if current_tokens + content_tokens > target_tokens and current_parts:
            flush()
            current_headings, current_parts, current_tokens = [], [], 0

        current_headings.append(heading)
        current_parts.append(f"### {heading}\n\n{content}")
        current_tokens += content_tokens

    flush()
    return merged


def chunk_file(filepath: Path):
    raw = filepath.read_text()
    title, body = parse_frontmatter(raw)
    department = filepath.parent.name
    raw_sections = split_into_sections(body)
    sections = merge_small_sections(raw_sections, TARGET_TOKENS, MAX_TOKENS)

    chunks = []
    for heading, content in sections:
        section_tokens = count_tokens(content)
        if section_tokens <= MAX_TOKENS:
            pieces = [content]
        else:
            pieces = split_long_section(content, TARGET_TOKENS, OVERLAP_TOKENS)

        display_heading = (
            "Full page"
            if len(raw_sections) > 1
            and len(sections) == 1
            else heading
        )

        for idx, piece in enumerate(pieces):
            if display_heading == "Full page":
                contextualized = f"# {title}\n\n{piece}"
            else:
                contextualized = f"# {title}\n## {heading}\n\n{piece}"

            chunk_id = (
                f"{filepath.stem}"
                f"::{display_heading.lower().replace(' ', '-').replace('/', '-')[:60]}"
                f"::{idx}"
            )

            chunks.append(Chunk(
                chunk_id=chunk_id,
                text=contextualized,
                source_file=str(filepath.relative_to(RAW)),
                department=department,
                page_title=title,
                section_heading=display_heading,
                chunk_index_in_section=idx,
                token_count=count_tokens(contextualized),
            ))

    return chunks


def main():
    all_chunks = []
    md_files = sorted(RAW.glob("**/*.md"))
    for f in md_files:
        all_chunks.extend(chunk_file(f))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as fh:
        for c in all_chunks:
            fh.write(json.dumps(asdict(c)) + "\n")

    token_counts = [c.token_count for c in all_chunks]
    print(f"Files processed : {len(md_files)}")
    print(f"Total chunks    : {len(all_chunks)}")
    print(f"Avg tokens/chunk: {sum(token_counts) / len(token_counts):.0f}")
    print(f"Min/Max tokens  : {min(token_counts)} / {max(token_counts)}")
    print(f"Output written  : {OUT}")


if __name__ == "__main__":
    main()