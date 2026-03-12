import re
from collections import OrderedDict


def clean_whitespace(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def naive_summary(text: str, max_sentences: int = 3) -> str:
    parts = re.split(r"(?<=[.!?])\s+", clean_whitespace(text))
    summary = " ".join([part for part in parts if part][:max_sentences])
    return summary.strip()


def dedupe_preserve_order(items: list[str]) -> list[str]:
    return list(OrderedDict((item, None) for item in items if item).keys())
