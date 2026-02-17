"""FlashCard screen for the flash card application."""

import random
import tkinter as tk

from ..base import BaseCardApp


class FlashCardApp(BaseCardApp):
    """Tkinter-based flash card application."""

    def __init__(self, root: tk.Tk, cards: list[dict], on_back_to_menu: callable = None, mode: str = "simple"):
        super().__init__(root, cards, on_back_to_menu)
        self.original_order = cards.copy()
        self.is_flipped = False
        self.mode = mode

        self._setup_ui()
        self._bind_keys()
        self._show_card()

    def _setup_ui(self):
        """Set up the user interface."""
        # Header with back button and title
        title_text = "Simple Mode" if self.mode == "simple" else "Inverted Mode"
        self._create_header(title_text)

        # Card area
        self.card_frame = self._create_card_frame()
        self.card_frame.bind("<Button-1>", lambda e: self._flip_card())

        # Term label (main content)
        self.term_label = tk.Label(
            self.card_frame,
            text="",
            font=("Helvetica", 22, "bold"),
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
        self.counter_label = self._create_counter_label(nav_frame)
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
            back_text = card["interpretation"]
            if card["extra"]:
                back_text += f"\n\n({card['extra']})"
            front_hint = "(click to flip)"
            back_hint = "(click to see term)"
            front_is_rtl = False
            back_is_rtl = True
        else:  # inverted mode
            front_text = card["interpretation"]
            back_text = card["term"]
            front_hint = "(click to flip)"
            back_hint = "(click to see interpretation)"
            front_is_rtl = True
            back_is_rtl = False

        if self.is_flipped:
            self._apply_dynamic_text_size(self.term_label, back_text, is_rtl=back_is_rtl)
            self.term_label.config(fg="#27ae60")
            self.hint_label.config(text=back_hint)
            self.card_frame.config(bg="#d5f5e3")
            self.term_label.config(bg="#d5f5e3")
            self.hint_label.config(bg="#d5f5e3")
        else:
            self._apply_dynamic_text_size(self.term_label, front_text, is_rtl=front_is_rtl)
            self.term_label.config(fg="#2c3e50")
            self.hint_label.config(text=front_hint)
            self.card_frame.config(bg="#ecf0f1")
            self.term_label.config(bg="#ecf0f1")
            self.hint_label.config(bg="#ecf0f1")

        self._update_counter()

    def _on_card_changed(self):
        """Called when the current card changes."""
        self.is_flipped = False
        self._show_card()

    def _flip_card(self):
        """Flip the current card."""
        self.is_flipped = not self.is_flipped
        self._show_card()

    def _next_card(self):
        """Go to the next card."""
        if self.cards and self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self._on_card_changed()

    def _prev_card(self):
        """Go to the previous card."""
        if self.cards and self.current_index > 0:
            self.current_index -= 1
            self._on_card_changed()

    def _shuffle_cards(self):
        """Shuffle the cards randomly."""
        random.shuffle(self.cards)
        self.current_index = 0
        self._on_card_changed()
