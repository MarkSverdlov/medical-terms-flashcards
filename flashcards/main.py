"""Main entry point for the flash card application."""

import tkinter as tk
from pathlib import Path

from .utils import parse_markdown_tables
from .controller import App


def main():
    """Main entry point."""
    # Find the markdown file relative to this script
    script_dir = Path(__file__).parent
    md_file = script_dir / "medical-terms.md"

    if not md_file.exists():
        print(f"Error: {md_file} not found")
        return

    # Parse cards
    cards = parse_markdown_tables(str(md_file))

    # Create and run the app
    root = tk.Tk()
    app = App(root, cards)
    root.mainloop()
