import torch
from transformers import pipeline

RELATIONSHIP_TYPES = [
    "friend",
    "enemy",
    "family",
    "romantic",
    "mentor",
    "servant",
    "colleague",
    "neutral",
]

CANDIDATE_LABELS = [
    "close friends and allies who support each other",
    "enemies and rivals who hate each other",
    "family relatives such as parent child sibling or spouse",
    "romantic lovers in a love relationship",
    "mentor and student or teacher and pupil",
    "master and servant or employer and worker",
    "professional colleagues who work together",
    "distant acquaintances with no strong bond",
]

LABEL_TO_TYPE = dict(zip(CANDIDATE_LABELS, RELATIONSHIP_TYPES))

DIRECTIONAL_TYPES = {"mentor", "servant"}

MODEL_NAME = "facebook/bart-large-mnli"


class RelationExtractor:
    def __init__(self):
        self._classifier = None
        self._loaded = False

    def load(self):
        self._classifier = pipeline(
            "zero-shot-classification",
            model=MODEL_NAME,
            device=-1,  # CPU
        )
        self._loaded = True

    @property
    def is_loaded(self):
        return self._loaded

    def classify_passages(
        self,
        passages: list[str],
        char_a: str,
        char_b: str,
        max_passages: int = 5,
    ) -> dict:
        if not self._loaded:
            self.load()

        sampled = passages[:max_passages]
        premise = " ".join(sampled)[:1500]

        sequence = f"The relationship between {char_a} and {char_b}: {premise}"

        result = self._classifier(
            sequence,
            candidate_labels=CANDIDATE_LABELS,
            multi_label=False,
        )

        top_label = result["labels"][0]
        top_score = result["scores"][0]
        best_type = LABEL_TO_TYPE[top_label]

        if best_type in DIRECTIONAL_TYPES:
            dir_result = self._classify_direction(premise, char_a, char_b, best_type)
            direction = dir_result
        else:
            direction = "bidirectional"

        return {
            "type": best_type,
            "confidence": round(top_score, 3),
            "direction": direction,
        }

    def _classify_direction(self, premise: str, char_a: str, char_b: str, rel_type: str) -> str:
        if rel_type == "mentor":
            labels = [
                f"{char_a} is the mentor or teacher of {char_b}",
                f"{char_b} is the mentor or teacher of {char_a}",
            ]
        else:
            labels = [
                f"{char_a} serves or works for {char_b}",
                f"{char_b} serves or works for {char_a}",
            ]

        result = self._classifier(premise, candidate_labels=labels, multi_label=False)
        if result["labels"][0] == labels[0]:
            return f"{char_a} -> {char_b}"
        return f"{char_b} -> {char_a}"


_extractor: RelationExtractor | None = None


def get_extractor() -> RelationExtractor:
    global _extractor
    if _extractor is None:
        _extractor = RelationExtractor()
        _extractor.load()
    return _extractor
