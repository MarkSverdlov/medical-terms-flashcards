"""Flash Card Game for Medical Terminology.

This module serves as a facade for backward compatibility.
All public symbols are re-exported from their respective modules.
"""

from .utils import fix_rtl, parse_markdown_tables
from .screens import MainMenu, FlashCardApp, QuizCardApp
from .controller import App
from .main import main

__all__ = [
    "fix_rtl",
    "parse_markdown_tables",
    "MainMenu",
    "FlashCardApp",
    "QuizCardApp",
    "App",
    "main",
]
