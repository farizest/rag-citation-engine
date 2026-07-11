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
# pyrefly: ignore [missing-import]
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
import fitz  # PyMuPDF
import nltk
# ── Dynamic model downloading ─────────────────────────────────
# This ensures that NLTK's sentence tokenization models are
# available on whatever machine runs this project.
try:
    nltk.data.find('tokenizers/punkt')
except Exception:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except Exception:
    try:
        nltk.download('punkt_tab', quiet=True)
    except Exception:
        pass  # punkt_tab is not needed or supported in older NLTK versions



ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "chunks.jsonl"

TARGET_TOKENS = 700
MAX_TOKENS = 800
OVERLAP_TOKENS = 100
WORDS_TO_TOKENS = 1.3


def count_tokens(text: str) -> int:
    return int(len(text.split()) * WORDS_TO_TOKENS)

def extract_pdf_text(filepath: Path) -> str:
    """
    Extract text page-by-page from a PDF file using PyMuPDF.
    Formats pages with a header prefix so the chunker treats each page
    as an individual structural section.
    """
    doc = fitz.open(str(filepath))
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages.append(f"## Page {i}\n\n{text.strip()}")
    return "\n\n".join(pages)


def split_into_sentences(text: str) -> list[str]:
    """
    Splits dense text into full grammatical sentences using NLTK.
    """
    return nltk.sent_tokenize(text)


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
    """
    Splits a long section into chunks using grammatical sentence boundaries.
    Applies sliding-window overlap using sentence groups.
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return [text]

    sub_chunks = []
    current_sents = []
    current_tokens = 0

    for sent in sentences:
        sent_tokens = count_tokens(sent)
        
        # If adding this sentence exceeds the token limit, save the chunk
        if current_tokens + sent_tokens > max_tokens and current_sents:
            sub_chunks.append(" ".join(current_sents))
            
            # ── sliding window overlap ────────────────────────────────
            # Backtrack and include previous sentences up to overlap_tokens
            overlap_sents = []
            overlap_count = 0
            for s in reversed(current_sents):
                st = count_tokens(s)
                if overlap_count + st > overlap_tokens:
                    break
                overlap_sents.insert(0, s)
                overlap_count += st
            current_sents = overlap_sents
            current_tokens = overlap_count

        current_sents.append(sent)
        current_tokens += sent_tokens

    if current_sents:
        sub_chunks.append(" ".join(current_sents))

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

def chunk_file(filepath: Path, override_title: str = None):
    """
    Reads a file (supporting PDF, MD, TXT), handles frontmatter or titles,
    splits it into sections, and yields contextualized Chunk objects.
    """
    # ── 1. Select the extraction method ───────────────────────────
    if filepath.suffix.lower() == ".pdf":
        raw = extract_pdf_text(filepath)
    else:
        # Using utf-8 with errors='ignore' ensures we don't crash on odd characters
        raw = filepath.read_text(encoding="utf-8", errors="ignore")

    title, body = parse_frontmatter(raw)
    if override_title:
        title = override_title
    
    # ── 2. Fall back to filename stem if there is no header ───────
    if not title:
        title = override_title or filepath.stem

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
            if len(raw_sections) > 1 and len(sections) == 1
            else heading
        )

        for idx, piece in enumerate(pieces):
            # Form contextualized chunk by prepending Title/Heading details
            if display_heading == "Full page":
                contextualized = f"# {title}\n\n{piece}"
            else:
                contextualized = f"# {title}\n## {heading}\n\n{piece}"

            chunk_id = (
                f"{filepath.name}"
                f"::{display_heading.lower().replace(' ', '-').replace('/', '-')[:60]}"
                f"::{idx}"
            )

            # Safely determine relative paths
            try:
                source_file = str(filepath.relative_to(RAW))
            except ValueError:
                source_file = filepath.name

            chunks.append(Chunk(
                chunk_id=chunk_id,
                text=contextualized,
                source_file=source_file,
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