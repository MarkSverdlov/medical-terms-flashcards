#!/usr/bin/env python3
"""Flash Card Game for Medical Terminology."""

import random
import tkinter as tk
from pathlib import Path
from bidi import get_display
import textwrap


def fix_rtl(text: str) -> str:
    # We do the wrapping manually outside of tkinter to handle peculiarities since the text is RTL
    lines = textwrap.wrap(text, width=25)
    return "\n".join([get_display(line) for line in lines])


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


class MainMenu:
    """Main menu screen."""

    def __init__(self, parent: tk.Frame, start_simple_mode: callable, start_inverted_mode: callable):
        self.frame = tk.Frame(parent, bg="#2c3e50")
        self.start_simple_mode = start_simple_mode
        self.start_inverted_mode = start_inverted_mode
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main menu UI."""
        # Title
        title_label = tk.Label(
            self.frame,
            text="Flash Card Game",
            font=("Helvetica", 28, "bold"),
            fg="white",
            bg="#2c3e50",
        )
        title_label.pack(pady=(80, 10))

        # Subtitle
        subtitle_label = tk.Label(
            self.frame,
            text="Medical Terminology",
            font=("Helvetica", 16),
            fg="#bdc3c7",
            bg="#2c3e50",
        )
        subtitle_label.pack(pady=(0, 50))

        # Simple Mode button
        simple_mode_btn = tk.Button(
            self.frame,
            text="Simple Mode",
            font=("Helvetica", 14),
            command=self.start_simple_mode,
            width=15,
            height=2,
        )
        simple_mode_btn.pack(pady=10)

        # Inverted Mode button
        inverted_mode_btn = tk.Button(
            self.frame,
            text="Inverted Mode",
            font=("Helvetica", 14),
            command=self.start_inverted_mode,
            width=15,
            height=2,
        )
        inverted_mode_btn.pack(pady=10)

    def show(self):
        """Show the main menu."""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide the main menu."""
        self.frame.pack_forget()


class FlashCardApp:
    """Tkinter-based flash card application."""

    def __init__(self, root: tk.Tk, cards: list[dict], on_back_to_menu: callable = None, mode: str = "simple"):
        self.root = root
        self.frame = tk.Frame(root, bg="#2c3e50")
        self.cards = cards
        self.original_order = cards.copy()
        self.current_index = 0
        self.is_flipped = False
        self.on_back_to_menu = on_back_to_menu
        self.mode = mode

        self._setup_ui()
        self._bind_keys()
        self._show_card()

    def _setup_ui(self):
        """Set up the user interface."""
        # Header with back button and title
        header_frame = tk.Frame(self.frame, bg="#2c3e50")
        header_frame.pack(fill=tk.X, pady=10)

        # Back to Menu button (left side)
        if self.on_back_to_menu:
            back_btn = tk.Button(
                header_frame,
                text="← Menu",
                font=("Helvetica", 10),
                command=self.on_back_to_menu,
            )
            back_btn.pack(side=tk.LEFT, padx=20)

        title_text = "Simple Mode" if self.mode == "simple" else "Inverted Mode"
        title_label = tk.Label(
            header_frame,
            text=title_text,
            font=("Helvetica", 20, "bold"),
            fg="white",
            bg="#2c3e50",
        )
        title_label.place(relx=0.5, rely=0.65, anchor="center")

        # Card area
        self.card_frame = tk.Frame(
            self.frame,
            bg="#ecf0f1",
            relief=tk.RAISED,
            borderwidth=3,
        )
        self.card_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        self.card_frame.bind("<Button-1>", lambda e: self._flip_card())

        # Term label (main content)
        self.term_label = tk.Label(
            self.card_frame,
            text="",
            font=("Helvetica", 28, "bold"),
            fg="#2c3e50",
            bg="#ecf0f1",
            wraplength=500,
            justify=tk.CENTER,
        )
        self.term_label.pack(expand=True, fill=tk.BOTH, pady=20)
        self.term_label.bind("<Button-1>", lambda e: self._flip_card())

        # Hint label
        self.hint_label = tk.Label(
            self.card_frame,
            text="(click to flip)",
            font=("Helvetica", 12, "italic"),
            fg="#7f8c8d",
            bg="#ecf0f1",
        )
        self.hint_label.pack(pady=(0, 15))
        self.hint_label.bind("<Button-1>", lambda e: self._flip_card())

        # Navigation frame
        nav_frame = tk.Frame(self.frame, bg="#2c3e50")
        nav_frame.pack(fill=tk.X, pady=10)

        # Previous button
        self.prev_btn = tk.Button(
            nav_frame,
            text="◀ Prev",
            font=("Helvetica", 12),
            command=self._prev_card,
            width=8,
        )
        self.prev_btn.pack(side=tk.LEFT, padx=20)

        # Counter label
        self.counter_label = tk.Label(
            nav_frame,
            text="",
            font=("Helvetica", 14),
            fg="white",
            bg="#2c3e50",
        )
        self.counter_label.pack(side=tk.LEFT, expand=True)

        # Next button
        self.next_btn = tk.Button(
            nav_frame,
            text="Next ▶",
            font=("Helvetica", 12),
            command=self._next_card,
            width=8,
        )
        self.next_btn.pack(side=tk.RIGHT, padx=20)

        # Shuffle button frame
        shuffle_frame = tk.Frame(self.frame, bg="#2c3e50")
        shuffle_frame.pack(fill=tk.X, pady=(0, 15))

        self.shuffle_btn = tk.Button(
            shuffle_frame,
            text="🔀 Shuffle",
            font=("Helvetica", 12),
            command=self._shuffle_cards,
            width=12,
        )
        self.shuffle_btn.pack()

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        self.root.bind("<Left>", lambda e: self._prev_card())
        self.root.bind("<Right>", lambda e: self._next_card())
        self.root.bind("<space>", lambda e: self._flip_card())
        self.root.bind("<Return>", lambda e: self._flip_card())

    def _show_card(self):
        """Display the current card."""
        if not self.cards:
            self.term_label.config(text="No cards loaded")
            self.counter_label.config(text="0 / 0")
            return

        card = self.cards[self.current_index]

        if self.mode == "simple":
            front_text = card["term"]
            back_text = fix_rtl(card["interpretation"])
            if card["extra"]:
                back_text += f"\n\n({fix_rtl(card['extra'])})"
            front_hint = "(click to flip)"
            back_hint = "(click to see term)"
        else:  # inverted mode
            front_text = fix_rtl(card["interpretation"])
            back_text = card["term"]
            front_hint = "(click to flip)"
            back_hint = "(click to see interpretation)"

        if self.is_flipped:
            self.term_label.config(text=back_text, fg="#27ae60")
            self.hint_label.config(text=back_hint)
            self.card_frame.config(bg="#d5f5e3")
            self.term_label.config(bg="#d5f5e3")
            self.hint_label.config(bg="#d5f5e3")
        else:
            self.term_label.config(text=front_text, fg="#2c3e50")
            self.hint_label.config(text=front_hint)
            self.card_frame.config(bg="#ecf0f1")
            self.term_label.config(bg="#ecf0f1")
            self.hint_label.config(bg="#ecf0f1")

        self.counter_label.config(
            text=f"Card {self.current_index + 1} of {len(self.cards)}"
        )

    def _flip_card(self):
        """Flip the current card."""
        self.is_flipped = not self.is_flipped
        self._show_card()

    def _next_card(self):
        """Go to the next card."""
        if self.cards and self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self.is_flipped = False
            self._show_card()

    def _prev_card(self):
        """Go to the previous card."""
        if self.cards and self.current_index > 0:
            self.current_index -= 1
            self.is_flipped = False
            self._show_card()

    def _shuffle_cards(self):
        """Shuffle the cards randomly."""
        random.shuffle(self.cards)
        self.current_index = 0
        self.is_flipped = False
        self._show_card()

    def show(self):
        """Show the flashcard screen."""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide the flashcard screen."""
        self.frame.pack_forget()


class App:
    """Main application managing screens."""

    def __init__(self, root: tk.Tk, cards: list[dict]):
        self.root = root
        self.cards = cards

        self.root.title("Flash Card Game - Medical Terminology")
        self.root.geometry("600x400")
        self.root.configure(bg="#2c3e50")

        # Create screens
        self.main_menu = MainMenu(self.root, self._start_simple_mode, self._start_inverted_mode)
        self.flashcard_app = None

        # Show main menu
        self.main_menu.show()

    def _start_simple_mode(self):
        """Switch to simple mode (flashcard game)."""
        self.main_menu.hide()

        # Create clone deck for the mode
        mode_cards = self.cards.copy()

        # Shuffle the deck
        random.shuffle(mode_cards)

        self.flashcard_app = FlashCardApp(self.root, mode_cards, self._back_to_menu, mode="simple")
        self.flashcard_app.show()

    def _start_inverted_mode(self):
        """Switch to inverted mode (flashcard game with swapped front/back)."""
        self.main_menu.hide()

        # Create clone deck for the mode
        mode_cards = self.cards.copy()

        # Shuffle the deck
        random.shuffle(mode_cards)

        self.flashcard_app = FlashCardApp(self.root, mode_cards, self._back_to_menu, mode="inverted")
        self.flashcard_app.show()

    def _back_to_menu(self):
        """Return to main menu."""
        if self.flashcard_app:
            self.flashcard_app.hide()
            self.flashcard_app = None
        self.main_menu.show()


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


if __name__ == "__main__":
    main()
