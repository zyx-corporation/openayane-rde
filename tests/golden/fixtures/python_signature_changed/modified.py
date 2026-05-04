"""Modified Python module fixture: function signature changed."""
import hashlib


def compute_hash(text: str) -> str:
    """Compute SHA-256 hash of text."""
    return hashlib.sha256(text.encode()).hexdigest()


def process_data(data: list[str]) -> list[str]:
    """Process a list of strings."""
    return [item for item in data if len(item) > 5]


class Evaluator:
    def evaluate(self, score: float) -> str:
        if score >= 0.8:
            return "pass"
        return "fail"
