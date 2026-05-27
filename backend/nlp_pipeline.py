import re
from collections import Counter

import spacy

nlp = spacy.load("en_core_web_sm")
nlp.max_length = 2_000_000

# ─── Titles & honorifics to strip from names ───
TITLES = {
    "Mr", "Mrs", "Ms", "Miss", "Dr", "Sir", "Lady", "Lord", "King",
    "Queen", "Prince", "Princess", "Captain", "Colonel", "Major",
    "General", "Reverend", "Rev", "Father", "Mother", "Brother",
    "Sister", "Uncle", "Aunt", "Monsieur", "Madame", "Mademoiselle",
    "Herr", "Frau", "Don", "Dona",
}
TITLE_PATTERN = re.compile(
    r"^(?:" + "|".join(re.escape(t) for t in TITLES) + r")\.?\s+", re.IGNORECASE
)

# ─── Names to always reject ───
STOP_NAMES = {
    "God", "Lord", "Christ", "Jesus", "Satan", "Devil",
    "Chapter", "Part", "Book", "Section", "Page", "Vol",
    "The", "Dear", "Amen", "Miss", "Madam", "Sir", "Sire",
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "English", "French", "German", "American", "British", "European",
    "Looky", "Heah", "Lordy", "Goodness",
}

# ─── OCR junk prefixes that appear before real names ───
OCR_PREFIXES = {
    "misto", "mars", "hap", "ir", "ole", "ol",
    "dat", "dis", "dem", "dey", "sah", "mos",
    "looky", "heah", "doan", "gwyne",
}

# ─── Ordinals / non-name words that appear as second token (OCR or misparse) ───
ORDINAL_WORDS = {
    "first", "second", "third", "fourth", "fifth", "sixth",
    "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth",
    "last", "next", "other", "same",
}

# ─── Common English place names (single-word) that spaCy often mislabels as PERSON ───
KNOWN_PLACES = {
    "London", "Paris", "Kent", "Bath", "Brighton", "Oxford", "Cambridge",
    "England", "France", "Ireland", "Scotland", "Wales", "America",
    "Rome", "Berlin", "Vienna", "Madrid", "Naples", "Florence",
    "Longbourn", "Netherfield", "Pemberley", "Rosings", "Meryton",
    "Hunsford", "Lambton", "Derbyshire", "Hertfordshire",
    "Mississippi", "Missouri", "Orleans", "Cairo", "Memphis",
    "Petersburg", "Boston", "Philadelphia", "Jerusalem",
}

# ─── Common English words that are unlikely to be standalone character names ───
COMMON_WORDS = {
    "Long", "Young", "Good", "Little", "Great", "Old", "New",
    "Rich", "Strong", "Sharp", "Short", "Grand", "Hardy",
    "Black", "White", "Green", "Brown", "Gray", "Grey",
    "Hill", "Dale", "Brook", "Stone", "Wood", "Cross",
    "Church", "West", "East", "North", "South",
    "Day", "Night", "Spring", "Summer", "Winter", "Fall",
}

# ─── "X of Y" patterns that are place/thing names, not people ───
OF_PATTERN = re.compile(r"^(\w+)\s+of\s+(\w+)$", re.IGNORECASE)

# ─── Regex filters for OCR noise, HTML ───
NOISE_RE = re.compile(
    r"[<>{}\[\]|/\\=;@#$%^&*~`]"
    r"|https?://"
    r"|www\."
    r"|class="
    r"|style[-_]"
    r"|\bscope\b"
    r"|\bsubnav\b"
    r"|\d{3,}",
    re.IGNORECASE,
)
ALLCAPS_RE = re.compile(r"\b[A-Z]{5,}\b")

TRAILING_PUNCT_RE = re.compile(r"[\.,;:!?\-'\"]+$")
LEADING_PUNCT_RE = re.compile(r"^[\.,;:!?\-'\"]+")

# ─── Common nickname → canonical first name mappings ───
KNOWN_NICKNAMES = {
    "Lizzy": "Elizabeth", "Liz": "Elizabeth", "Beth": "Elizabeth",
    "Eliza": "Elizabeth", "Bess": "Elizabeth", "Bessie": "Elizabeth",
    "Dick": "Richard", "Rick": "Richard",
    "Bill": "William", "Will": "William", "Willy": "William", "Billy": "William",
    "Tom": "Thomas", "Tommy": "Thomas",
    "Bob": "Robert", "Bobby": "Robert", "Rob": "Robert",
    "Jim": "James", "Jimmy": "James", "Jamie": "James",
    "Jack": "John", "Johnny": "John", "Jon": "John",
    "Kate": "Katherine", "Katie": "Katherine", "Kathy": "Katherine",
    "Kit": "Katherine", "Kitty": "Katherine",
    "Meg": "Margaret", "Maggie": "Margaret", "Peggy": "Margaret",
    "Nick": "Nicholas", "Nicky": "Nicholas",
    "Ted": "Edward", "Teddy": "Edward", "Ned": "Edward",
    "Ed": "Edward", "Eddie": "Edward",
    "Harry": "Henry", "Hal": "Henry", "Hank": "Henry",
    "Charlie": "Charles", "Chuck": "Charles", "Charley": "Charles",
    "Sally": "Sarah", "Sal": "Sarah",
    "Jenny": "Jennifer", "Jen": "Jennifer",
    "Dan": "Daniel", "Danny": "Daniel",
    "Mike": "Michael", "Mick": "Michael",
    "Pat": "Patrick", "Paddy": "Patrick",
    "Alex": "Alexander", "Sandy": "Alexander",
    "Sam": "Samuel", "Sammy": "Samuel",
    "Ben": "Benjamin", "Benny": "Benjamin",
    "Joe": "Joseph", "Joey": "Joseph",
    "Frank": "Francis", "Fanny": "Frances",
}


def _clean_name(raw: str) -> str | None:
    name = raw.strip()
    name = re.sub(r"-\s+", "", name)
    name = LEADING_PUNCT_RE.sub("", name)
    name = TRAILING_PUNCT_RE.sub("", name)
    name = re.sub(r"[‘’’’`]\s*s?\s*$", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = TITLE_PATTERN.sub("", name).strip()

    if len(name) < 2:
        return None
    if name in STOP_NAMES:
        return None
    if name in KNOWN_PLACES:
        return None
    if NOISE_RE.search(name):
        return None
    if ALLCAPS_RE.search(name):
        return None
    if not name[0].isupper():
        return None

    parts = name.split()

    if all(len(p) <= 1 for p in parts):
        return None

    # Reject non-name content words
    if any(w in name for w in ("Memoir", "Neither", "Chapter", "Volume", "Preface", "Introduction")):
        return None

    # ─── OCR prefix filter ───
    # "Misto Tom", "Mars Buck", "Hap Elizabeth" → strip the junk prefix
    if len(parts) >= 2 and parts[0].lower() in OCR_PREFIXES:
        parts = parts[1:]
        name = " ".join(parts)
        if not name or not name[0].isupper():
            return None

    # ─── Ordinal/non-name word in any position ───
    # "James Second", "William Fourth" → strip the ordinal
    new_parts = [p for p in parts if p.lower() not in ORDINAL_WORDS]
    if len(new_parts) < len(parts):
        parts = new_parts
        name = " ".join(parts)
        if not name:
            return None

    # Short lowercase tokens that aren’t prepositions
    allowed_short = {"de", "du", "le", "la", "of", "von", "van", "al", "el", "di", "da"}
    for p in parts:
        if len(p) <= 2 and p.lower() not in allowed_short and not p[0].isupper():
            return None

    # Single-word place-name suffixes
    if len(parts) == 1:
        if re.search(
            r"(bourne?|field|shire|town|land|burg|ford|ham|ley|wood|park|hall|castle|bridge|minster|mouth|pool|wick|stead)$",
            name, re.IGNORECASE
        ):
            return None

    # "X of Y" where Y looks like a place (capitalized, ends in place suffix, or is known)
    m = OF_PATTERN.match(name)
    if m:
        y_word = m.group(2)
        if y_word in KNOWN_PLACES:
            return None
        if re.search(r"(shire|ham|bury|ton|ley|land|stead)$", y_word, re.IGNORECASE):
            return None

    # OCR noise: dot followed by lowercase
    if re.search(r"\.[a-z]", name):
        return None

    # Single-word names that are too short (likely not real character names)
    if len(parts) == 1 and len(name) <= 3:
        return None

    # Single-word names that are common English words (not character names)
    if len(parts) == 1 and name in COMMON_WORDS:
        return None

    # Too many words — likely OCR concatenation of multiple names
    if len(parts) > 3:
        return None

    if len(name) < 2:
        return None

    return name


def _normalize(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(r"[‘’`’’]s?$", "", n)
    # Only strip obvious plural "es" suffix (Collinses→Collins, Phillipses→Phillips)
    # Don’t strip single "s" — names like "Collins", "James", "Charles" end in s naturally
    if n.endswith("es") and len(n) > 5 and not n.endswith("mes") and not n.endswith("les"):
        n = n[:-2]
    return n


def extract_characters(text: str, max_chars: int = 500_000) -> tuple[list[str], dict[str, set[str]]]:
    """Returns (canonical_names, alias_map) where alias_map[canonical] = {all variants}."""
    # Skip front/back matter (prefaces, endnotes) — analyze middle 85%
    text = text[:max_chars]
    total_len = len(text)
    skip_front = total_len * 8 // 100
    skip_back = total_len * 7 // 100
    body = text[skip_front:total_len - skip_back] if total_len > 20000 else text
    doc = nlp(body)

    # Count how often each name appears as PERSON vs non-PERSON entity
    person_counts: Counter = Counter()
    non_person_counts: Counter = Counter()
    for ent in doc.ents:
        cleaned = _clean_name(ent.text)
        if not cleaned:
            continue
        if ent.label_ == "PERSON":
            person_counts[cleaned] += 1
        elif ent.label_ in ("GPE", "LOC", "ORG", "FAC", "EVENT", "WORK_OF_ART", "PRODUCT", "NORP"):
            non_person_counts[cleaned] += 1

    # Exclude names that appear more as non-person than person
    raw_counts: Counter = Counter()
    for name, count in person_counts.items():
        if non_person_counts.get(name, 0) >= count:
            continue
        raw_counts[name] = count

    if not raw_counts:
        return [], {}

    # Merge: longest form preferred as canonical
    canonical_list, alias_map = _merge_all(raw_counts)

    # Apply known nickname mappings
    canonical_list, alias_map = _apply_nicknames(canonical_list, alias_map)

    # Filter by minimum frequency
    total_mentions = sum(raw_counts[a] for aliases in alias_map.values() for a in aliases)
    min_count = max(3, total_mentions // 200)
    filtered = []
    for name in canonical_list:
        mentions = sum(raw_counts.get(a, 0) for a in alias_map.get(name, {name}))
        if mentions >= min_count:
            filtered.append(name)

    return filtered[:20], {k: v for k, v in alias_map.items() if k in filtered[:20]}


def _merge_all(counts: Counter) -> tuple[list[str], dict[str, set[str]]]:
    def _sort_key(n):
        # Prefer base forms (non-plural) as canonical, then longest, then most frequent
        norm = _normalize(n)
        is_plural = 1 if norm != n.lower() else 0
        return (is_plural, -len(n), -counts[n])

    names = sorted(counts.keys(), key=_sort_key)
    canonical_norms: dict[str, str] = {}
    alias_map: dict[str, set[str]] = {}
    merged_counts: Counter = Counter()

    for name in names:
        norm = _normalize(name)
        matched = None
        best_score = 0
        best_count = 0
        candidates_at_best = 0

        for canon, canon_norm in canonical_norms.items():
            score = _merge_score(name, norm, canon, canon_norm)
            if score > 0:
                if score > best_score:
                    best_score = score
                    best_count = merged_counts[canon]
                    matched = canon
                    candidates_at_best = 1
                elif score == best_score:
                    candidates_at_best += 1
                    if merged_counts[canon] > best_count:
                        best_count = merged_counts[canon]
                        matched = canon

        # If multiple canonicals match with same low score, don't merge (ambiguous first-name)
        if candidates_at_best > 1 and best_score <= 42:
            matched = None

        if matched:
            alias_map[matched].add(name)
            merged_counts[matched] += counts[name]
        else:
            canonical_norms[name] = norm
            alias_map[name] = {name}
            merged_counts[name] = counts[name]

    ranked = [n for n, _ in merged_counts.most_common()]
    return ranked, alias_map


def _merge_score(name: str, norm: str, canon: str, canon_norm: str) -> int:
    """Return 0 if names should NOT merge, or a positive score (higher = better match)."""
    if norm == canon_norm:
        return 100

    name_parts = name.split()
    canon_parts = canon.split()

    # Single word matching a word in multi-word name
    if len(name_parts) == 1 and len(canon_parts) > 1:
        word = name_parts[0].lower()
        # Surname match scores higher than first-name match
        if word == canon_parts[-1].lower():
            return 50 + len(canon_parts)
        if word == canon_parts[0].lower():
            return 40 + len(canon_parts)
        if name_parts[0] in KNOWN_NICKNAMES:
            target = KNOWN_NICKNAMES[name_parts[0]]
            if canon_parts[0].lower() == target.lower():
                return 45
        return 0

    if len(canon_parts) == 1 and len(name_parts) > 1:
        word = canon_parts[0].lower()
        if word == name_parts[-1].lower():
            return 50 + len(name_parts)
        if word == name_parts[0].lower():
            return 40 + len(name_parts)
        return 0

    # Both multi-word: merge only if they share the same surname AND a first name component
    # OR one is a prefix of the other ("Mary Jane" ⊂ "Mary Jane Wilks")
    if len(name_parts) > 1 and len(canon_parts) > 1:
        # Prefix match: shorter is exact prefix of longer
        shorter = name_parts if len(name_parts) <= len(canon_parts) else canon_parts
        longer = canon_parts if len(name_parts) <= len(canon_parts) else name_parts
        if all(shorter[i].lower() == longer[i].lower() for i in range(len(shorter))):
            return 85

        if name_parts[-1].lower() == canon_parts[-1].lower():
            name_first = set(w.lower() for w in name_parts[:-1])
            canon_first = set(w.lower() for w in canon_parts[:-1])
            if name_first & canon_first:
                return 80
            for nw in name_first:
                target = KNOWN_NICKNAMES.get(nw.capitalize(), "").lower()
                if target and target in canon_first:
                    return 70
            for cw in canon_first:
                target = KNOWN_NICKNAMES.get(cw.capitalize(), "").lower()
                if target and target in name_first:
                    return 70
        return 0

    # Normalized substring check for single-word to single-word
    # Only match if the shorter IS a complete word in the longer (word boundary)
    if len(name_parts) == 1 and len(canon_parts) == 1:
        if len(norm) >= 5 and len(canon_norm) >= 5:
            if norm == canon_norm:
                return 30

    return 0


def _apply_nicknames(canonical_list: list[str], alias_map: dict[str, set[str]]) -> tuple[list[str], dict[str, set[str]]]:
    """Merge standalone nicknames into their full-name canonical when both exist."""
    to_remove = set()
    for name in list(canonical_list):
        first_word = name.split()[0]
        target_first = KNOWN_NICKNAMES.get(first_word)
        if not target_first:
            continue
        # Find a canonical that starts with the target first name
        for canon in canonical_list:
            if canon == name:
                continue
            if canon.split()[0].lower() == target_first.lower():
                alias_map[canon] |= alias_map.pop(name, {name})
                to_remove.add(name)
                break

    result = [n for n in canonical_list if n not in to_remove]
    return result, alias_map


def build_relationships(text: str, characters: list[str], alias_map: dict[str, set[str]], window: int = 3) -> list[dict]:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
    co_occur: Counter = Counter()

    for i in range(0, len(paragraphs), window):
        chunk = " ".join(paragraphs[i:i + window])
        present = []
        for canon in characters:
            aliases = alias_map.get(canon, {canon})
            if any(a in chunk for a in aliases):
                present.append(canon)

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
