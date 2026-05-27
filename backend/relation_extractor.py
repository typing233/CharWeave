import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

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

HYPOTHESES = {
    "friend": "{A} and {B} are friends or allies.",
    "enemy": "{A} and {B} are enemies or rivals.",
    "family": "{A} and {B} are family members or relatives.",
    "romantic": "{A} and {B} are in a romantic relationship or are lovers.",
    "mentor": "{A} is a mentor, teacher, or guide to {B}.",
    "servant": "{A} is a servant, employee, or subordinate of {B}.",
    "colleague": "{A} and {B} are colleagues or professional associates.",
    "neutral": "{A} and {B} are acquaintances with no strong relationship.",
}

DIRECTIONAL_TYPES = {"mentor", "servant"}

MODEL_NAME = "cross-encoder/nli-deberta-v3-base"


class RelationExtractor:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self._loaded = False

    def load(self):
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
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
        premise = " ".join(sampled)[:2000]

        scores = self._batch_score(premise, char_a, char_b)

        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        if best_type in DIRECTIONAL_TYPES:
            rev_scores = self._batch_score(premise, char_b, char_a)
            rev_confidence = rev_scores[best_type]
            if rev_confidence > confidence:
                direction = f"{char_b} -> {char_a}"
                confidence = rev_confidence
            else:
                direction = f"{char_a} -> {char_b}"
        else:
            direction = "bidirectional"

        return {
            "type": best_type,
            "confidence": round(confidence, 3),
            "direction": direction,
        }

    def _batch_score(self, premise: str, char_a: str, char_b: str) -> dict[str, float]:
        hypotheses = []
        type_order = []
        for rel_type, template in HYPOTHESES.items():
            hypotheses.append(template.format(A=char_a, B=char_b))
            type_order.append(rel_type)

        inputs = self.tokenizer(
            [premise] * len(hypotheses),
            hypotheses,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        with torch.no_grad():
            logits = self.model(**inputs).logits

        # NLI labels: [contradiction, neutral, entailment]
        probs = torch.softmax(logits, dim=1)
        entailment_scores = probs[:, 2].tolist()

        return dict(zip(type_order, entailment_scores))


_extractor: RelationExtractor | None = None


def get_extractor() -> RelationExtractor:
    global _extractor
    if _extractor is None:
        _extractor = RelationExtractor()
        _extractor.load()
    return _extractor
