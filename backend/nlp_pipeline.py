import re
from collections import Counter, defaultdict

import spacy

nlp = spacy.load("en_core_web_sm")
nlp.max_length = 2_000_000

STOP_NAMES = {
    "God", "Lord", "Sir", "Mr", "Mrs", "Miss", "Chapter",
    "Part", "Book", "Section", "Page", "The", "Dear",
}

NOISE_PATTERNS = re.compile(
    r"(class=|style-scope|href=|<[a-z]|/>|subnav|fff|div|span|http|www\.|"
    r"Neither|Memoir|Chapter|'s$|^\d)", re.IGNORECASE
)


def extract_characters(text: str, max_chars: int = 500_000) -> list[str]:
    text = text[:max_chars]
    doc = nlp(text)
    name_counts: Counter = Counter()
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            name = re.sub(r"\s+", " ", name)
            if len(name) > 1 and name not in STOP_NAMES and not name.isdigit() and not NOISE_PATTERNS.search(name):
                name_counts[name] += 1

    merged = _merge_names(name_counts)
    top = merged.most_common(20)
    return [name for name, _ in top]


def _merge_names(counts: Counter) -> Counter:
    names = sorted(counts.keys(), key=len, reverse=True)
    canonical: dict[str, str] = {}
    merged = Counter()

    for name in names:
        found = False
        for canon in canonical.values():
            if name in canon or canon in name:
                merged[canon] += counts[name]
                canonical[name] = canon
                found = True
                break
        if not found:
            canonical[name] = name
            merged[name] += counts[name]

    return merged


def build_relationships(text: str, characters: list[str], window: int = 3) -> list[dict]:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
    co_occur: Counter = Counter()

    for i in range(0, len(paragraphs), window):
        chunk = " ".join(paragraphs[i:i + window])
        present = [c for c in characters if c in chunk]
        for a_idx in range(len(present)):
            for b_idx in range(a_idx + 1, len(present)):
                pair = tuple(sorted([present[a_idx], present[b_idx]]))
                co_occur[pair] += 1

    relationships = []
    for (a, b), weight in co_occur.most_common(30):
        relationships.append({"source": a, "target": b, "weight": weight})
    return relationships


def generate_mermaid(characters: list[str], relationships: list[dict]) -> str:
    lines = ["graph TD"]
    node_ids: dict[str, str] = {}
    for i, name in enumerate(characters):
        node_id = f"C{i}"
        node_ids[name] = node_id
        safe_name = name.replace('"', "'")
        lines.append(f'    {node_id}["{safe_name}"]')

    for rel in relationships:
        src = node_ids.get(rel["source"])
        tgt = node_ids.get(rel["target"])
        if src and tgt:
            label = str(rel["weight"])
            lines.append(f"    {src} -->|{label}| {tgt}")

    return "\n".join(lines)
