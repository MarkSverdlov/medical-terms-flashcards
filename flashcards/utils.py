"""Utility functions for the flash card application."""

from pathlib import Path

from bidi import get_display
import textwrap


def fix_rtl(text: str, wrap_width: int = 25) -> str:
    """Fix right-to-left text display by wrapping and applying bidi algorithm."""
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


def parse_markdown_tables(filepath: str) -> list[dict]:
    """Parse markdown tables from file and return list of flash cards."""
    cards = []
    content = Path(filepath).read_text(encoding="utf-8")
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Check if this is a table header row (starts with |)
        if line.startswith("|") and "|" in line[1:]:
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
                        }
                        cards.append(card)
                    i += 1
                continue
        i += 1

    return cards
