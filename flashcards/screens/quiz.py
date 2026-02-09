"""Quiz screen for the flash card application."""

import tkinter as tk

from ..base import BaseCardApp
from ..utils import fix_rtl


class QuizCardApp(BaseCardApp):
    """Quiz mode - type the term for the shown interpretation."""

    def __init__(self, root: tk.Tk, cards: list[dict], on_back_to_menu: callable = None):
        super().__init__(root, cards, on_back_to_menu)
        self.current_answered = False

        self._setup_ui()
        self._bind_keys()
        self._show_card()

    def _setup_ui(self):
        """Set up the user interface."""
        # Header with back button and title
        self._create_header("Quiz Mode")

        # Card area (non-clickable)
        self.card_frame = self._create_card_frame()

        # Interpretation label (main content)
        self.interpretation_label = tk.Label(
            self.card_frame,
            text="",
            font=("Helvetica", 22, "bold"),
            fg="#2c3e50",
            bg="#ecf0f1",
            wraplength=500,
            justify=tk.CENTER,
        )
        self.interpretation_label.pack(expand=True, fill=tk.BOTH, pady=20)

        # Hint label
        self.hint_label = tk.Label(
            self.card_frame,
            text="(type the medical term)",
            font=("Helvetica", 12, "italic"),
            fg="#7f8c8d",
            bg="#ecf0f1",
        )
        self.hint_label.pack(pady=(0, 15))

        # Entry frame
        entry_frame = tk.Frame(self.frame, bg="#2c3e50")
        entry_frame.pack(fill=tk.X, pady=10)

        self.entry = tk.Entry(
            entry_frame,
            font=("Helvetica", 16),
            width=30,
            justify=tk.CENTER,
        )
        self.entry.pack(pady=5)

        # Submit button
        self.submit_btn = tk.Button(
            entry_frame,
            text="Submit",
            font=("Helvetica", 12),
            command=self._submit_answer,
            width=10,
        )
        self.submit_btn.pack(pady=5)

        # Result frame (container for styled feedback)
        self.result_frame = tk.Frame(self.frame, bg="#2c3e50")
        self.result_frame.pack(fill=tk.X, padx=30, pady=5)

        # Inner result box (will be colored on answer)
        self.result_box = tk.Frame(self.result_frame, padx=15, pady=8)
        self.result_box.pack()

        # Message label (e.g., "Correct!" or "Incorrect. Answer:")
        self.result_msg_label = tk.Label(
            self.result_box,
            text="",
            font=("Helvetica", 14),
        )
        self.result_msg_label.pack(side=tk.LEFT)

        # Term label (bold, for emphasized terms)
        self.result_term_label = tk.Label(
            self.result_box,
            text="",
            font=("Helvetica", 14, "bold"),
        )
        self.result_term_label.pack(side=tk.LEFT)

        # Counter label
        self.counter_label = self._create_counter_label(self.frame)
        self.counter_label.pack(pady=10)

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        self.root.bind("<Return>", lambda e: self._handle_return())

    def _show_card(self):
        """Display the current card."""
        if not self.cards:
            self.interpretation_label.config(text="No cards loaded")
            self.counter_label.config(text="0 / 0")
            return

        card = self.cards[self.current_index]
        self.interpretation_label.config(text=fix_rtl(card["interpretation"]))

        # Clear input and result
        self.entry.delete(0, tk.END)
        self._clear_feedback()
        self.current_answered = False

        self._update_counter()

        # Focus the entry field
        self.entry.focus_set()

    def _on_card_changed(self):
        """Called when the current card changes."""
        self._show_card()

    def _submit_answer(self):
        """Check the user's answer."""
        if self.current_answered:
            return

        user_answer = self.entry.get().strip().lower().replace("-", "")
        correct_term = self.cards[self.current_index]["term"]

        self.current_answered = True

        # Normalize for comparison (ignore dashes)
        def normalize(s):
            return s.strip().lower().replace("-", "")

        # Parse comma-separated terms into sets
        user_terms = {normalize(t) for t in user_answer.split(",") if normalize(t)}
        correct_terms = {normalize(t) for t in correct_term.split(",") if normalize(t)}

        if user_terms == correct_terms:
            self._show_feedback("Correct!", "", is_correct=True)
        elif user_terms and user_terms.issubset(correct_terms):
            self._show_feedback("Correct! Full answer: ", correct_term, is_correct=True)
        else:
            self._show_feedback("Incorrect. Answer: ", correct_term, is_correct=False)

    def _show_feedback(self, message: str, term: str, is_correct: bool):
        """Display styled feedback with colored background."""
        bg_color = "#27ae60" if is_correct else "#e74c3c"  # green or red

        self.result_box.config(bg=bg_color)
        self.result_msg_label.config(text=message, bg=bg_color, fg="white")
        self.result_term_label.config(text=term, bg=bg_color, fg="white")

    def _clear_feedback(self):
        """Clear the feedback display."""
        self.result_box.config(bg="#2c3e50")
        self.result_msg_label.config(text="", bg="#2c3e50")
        self.result_term_label.config(text="", bg="#2c3e50")

    def _handle_return(self):
        """Handle Return key - submit if not answered, next card if answered."""
        if self.current_answered:
            self._next_card()
        else:
            self._submit_answer()
