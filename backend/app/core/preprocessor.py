import re
from bs4 import BeautifulSoup
from typing import Tuple, Optional
from app.utils.logger import logger

class TextPreprocessor:
    """Cleans, sanitizes, and normalizes raw article text and HTML."""

    @staticmethod
    def clean_html(raw_html: Optional[str]) -> str:
        """Strips HTML tags and decodes entities safely."""
        if not raw_html or not raw_html.strip():
            return ""

        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            # Remove scripts, styles, iframes, and ads
            for tag in soup(["script", "style", "noscript", "iframe", "header", "footer"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return TextPreprocessor.normalize_whitespace(text)
        except Exception as e:
            logger.warning(f"HTML parsing fallback due to: {e}")
            clean = re.sub(r"<[^>]+>", " ", raw_html)
            return TextPreprocessor.normalize_whitespace(clean)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Collapses duplicate whitespace, tabs, and newlines."""
        if not text:
            return ""
        text = text.replace("\xa0", " ").replace("\u200b", "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def clean_article(
        cls,
        raw_title: str,
        raw_summary: Optional[str] = None,
        raw_content: Optional[str] = None
    ) -> Tuple[str, str, str, bool]:
        """
        Cleans title, summary, and content.
        Returns (cleaned_title, cleaned_summary, cleaned_content, is_valid).
        """
        cleaned_title = cls.clean_html(raw_title)
        cleaned_summary = cls.clean_html(raw_summary)
        cleaned_content = cls.clean_html(raw_content)

        # If content is missing, fallback to summary
        if not cleaned_content or len(cleaned_content) < len(cleaned_summary):
            cleaned_content = cleaned_summary

        # Check minimal validity
        is_valid = len(cleaned_title) >= 5 and len(cleaned_content) >= 30

        return cleaned_title, cleaned_summary, cleaned_content, is_valid

