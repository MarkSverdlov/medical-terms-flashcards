"""Base class for card application screens."""

import tkinter as tk
from abc import ABC, abstractmethod


class BaseCardApp(ABC):
    """Abstract base class for card-based screens (FlashCard and Quiz modes)."""

    def __init__(self, root: tk.Tk, cards: list[dict], on_back_to_menu: callable = None):
        self.root = root
        self.frame = tk.Frame(root, bg="#2c3e50")
        self.cards = cards
        self.current_index = 0
        self.on_back_to_menu = on_back_to_menu

    def _create_header(self, title_text: str) -> tk.Frame:
        """Create header frame with back button and title."""
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

        title_label = tk.Label(
            header_frame,
            text=title_text,
            font=("Helvetica", 20, "bold"),
            fg="white",
            bg="#2c3e50",
        )
        title_label.place(relx=0.5, rely=0.65, anchor="center")

        return header_frame

    def _create_card_frame(self) -> tk.Frame:
        """Create the card display frame."""
        card_frame = tk.Frame(
            self.frame,
            bg="#ecf0f1",
            relief=tk.RAISED,
            borderwidth=3,
        )
        card_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        return card_frame

    def _create_counter_label(self, parent: tk.Frame) -> tk.Label:
        """Create the card counter label."""
        counter_label = tk.Label(
            parent,
            text="",
            font=("Helvetica", 14),
            fg="white",
            bg="#2c3e50",
        )
        return counter_label

    def _update_counter(self):
        """Update the counter label with current position."""
        if not self.cards:
            self.counter_label.config(text="0 / 0")
        else:
            self.counter_label.config(
                text=f"Card {self.current_index + 1} of {len(self.cards)}"
            )

    def _next_card(self):
        """Go to the next card."""
        if self.cards and self.current_index < len(self.cards) - 1:
            self.current_index += 1
            self._on_card_changed()

    @abstractmethod
    def _on_card_changed(self):
        """Hook called when the current card changes. Subclasses must implement."""
        pass

    @abstractmethod
    def _setup_ui(self):
        """Set up the user interface. Subclasses must implement."""
        pass

    def show(self):
        """Show the screen."""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide the screen."""
        self.frame.pack_forget()
