"""Utility functions for the flash card application."""

import random
from collections import defaultdict
from pathlib import Path

from bidi import get_display
import textwrap


def spread_shuffle_with_replacement(cards: list[dict], k: int) -> list[dict]:
    """Sample k cards with replacement, then spread sections apart.

    This creates a "humanly random" shuffle by:
    1. Sampling k cards with replacement (allowing duplicates)
    2. Grouping by section and shuffling within each section
    3. Round-robin merging to spread cards from the same section apart

    Args:
        cards: List of card dictionaries with 'section' key
        k: Number of cards to sample

    Returns:
        A list of k cards with sections spread apart
    """
    if not cards:
        return []

    # Sample with replacement
    sampled = random.choices(cards, k=k)

    return spread_shuffle(sampled)


def spread_shuffle(cards: list[dict]) -> list[dict]:
    """Shuffle cards while spreading sections apart.

    Groups cards by section, shuffles within each group, then round-robin
    merges to minimize consecutive cards from the same section.

    Args:
        cards: List of card dictionaries with 'section' key

    Returns:
        A new list with cards spread by section
    """
    if not cards:
        return []

    # Group by section
    by_section = defaultdict(list)
    for card in cards:
        by_section[card.get('section', '')].append(card)

    # Shuffle within each section group
    for section_cards in by_section.values():
        random.shuffle(section_cards)

    # Round-robin merge from each section
    result = []
    sections = list(by_section.values())
    random.shuffle(sections)  # randomize section order

    while any(sections):
        for section_cards in sections:
            if section_cards:
                result.append(section_cards.pop())

    return result


def fix_rtl(text: str, wrap_width: int = 25) -> str:
    """Fix right-to-left text display by wrapping and applying bidi algorithm."""
    if wrap_width is None:
        return get_display(text)
    # We do the wrapping manually outside of tkinter to handle peculiarities since the text is RTL
    lines = textwrap.wrap(text, width=wrap_width)
    return "\n".join([get_display(line) for line in lines])


def calculate_font_size(text: str) -> dict:
    """Calculate font size and wrap settings based on text length."""
    text_len = len(text.replace('\n', ''))

    if text_len <= 30:
        return {'font_size': 22, 'wrap_chars': 25, 'wraplength': 500}
    elif text_len <= 60:
        return {'font_size': 18, 'wrap_chars': 30, 'wraplength': 450}
    elif text_len <= 100:
        return {'font_size': 16, 'wrap_chars': 35, 'wraplength': 420}
    elif text_len <= 150:
        return {'font_size': 14, 'wrap_chars': 40, 'wraplength': 400}
    else:
        return {'font_size': 12, 'wrap_chars': 45, 'wraplength': 380}


def parse_markdown_tables(filepath: str) -> tuple[list[dict], list[str]]:
    """Parse markdown tables from file and return list of flash cards with sections."""
    cards = []
    sections = []
    current_section = "General"
    content = Path(filepath).read_text(encoding="utf-8")
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for section title (line followed by ====)
        if i + 1 < len(lines) and lines[i + 1].strip().startswith("===="):
            current_section = line
            if current_section not in sections:
                sections.append(current_section)
            i += 2
            continue

        # Check if this is a table header row (starts with |)
        if line.startswith("|") and "|" in line[1:]:
            if current_section not in sections:
                sections.append(current_section)
            # Skip the separator line (contains ----)
            if i + 1 < len(lines) and "----" in lines[i + 1]:
                i += 2  # Move past header and separator
                # Parse table rows
                while i < len(lines):
                    row = lines[i].strip()
                    if not row.startswith("|"):
                        break
                    # Split by | and clean up
                    cells = [c.strip() for c in row.split("|")]
                    # Remove empty strings from split
                    cells = [c for c in cells if c or cells.index(c) not in [0, len(cells) - 1]]
                    cells = [c for c in cells if c]

                    if len(cells) >= 2:
                        card = {
                            "term": cells[0],
                            "interpretation": cells[1],
                            "extra": cells[2] if len(cells) > 2 else "",
                            "section": current_section,
                        }
                        cards.append(card)
                    i += 1
                continue
        i += 1

    return cards, sections
