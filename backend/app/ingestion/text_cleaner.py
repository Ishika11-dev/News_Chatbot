"""
HTML cleaning and text normalization utilities.
"""

import re
from typing import Optional
from bs4 import BeautifulSoup


def clean_html(raw_html: Optional[str]) -> str:
    """
    Strips HTML tags and normalizes whitespace safely.
    Removes script, style, noscript, and iframe elements.
    """
    if not raw_html or not raw_html.strip():
        return ""

    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", raw_html)

    return normalize_whitespace(text)


def normalize_whitespace(text: str) -> str:
    """Collapses duplicate spaces, tabs, and non-breaking spaces."""
    if not text:
        return ""
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class TextCleaner:
    """Utility class providing static text cleaning methods."""

    @staticmethod
    def clean_html(raw_html: Optional[str]) -> str:
        return clean_html(raw_html)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        return normalize_whitespace(text)
