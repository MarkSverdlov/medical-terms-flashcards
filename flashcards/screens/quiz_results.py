"""Quiz results screen for the flash card application."""

import tkinter as tk


class QuizResultsScreen:
    """Screen displaying quiz completion summary."""

    def __init__(
        self,
        root: tk.Tk,
        correct_count: int,
        total: int,
        on_back_to_menu: callable = None,
    ):
        self.root = root
        self.correct_count = correct_count
        self.total = total
        self.on_back_to_menu = on_back_to_menu

        self.frame = tk.Frame(root, bg="#2c3e50")
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Title
        title_label = tk.Label(
            self.frame,
            text="Quiz Complete!",
            font=("Helvetica", 28, "bold"),
            fg="white",
            bg="#2c3e50",
        )
        title_label.pack(pady=(60, 30))

        # Score display
        percentage = (self.correct_count / self.total * 100) if self.total > 0 else 0
        score_text = f"You got {self.correct_count} out of {self.total} correct ({percentage:.0f}%)"
        score_label = tk.Label(
            self.frame,
            text=score_text,
            font=("Helvetica", 18),
            fg="white",
            bg="#2c3e50",
        )
        score_label.pack(pady=20)

        # Return to Menu button
        menu_btn = tk.Button(
            self.frame,
            text="Return to Menu",
            font=("Helvetica", 14),
            command=self.on_back_to_menu,
            width=15,
            height=2,
        )
        menu_btn.pack(pady=30)

        # Bind Enter key to return to menu
        self.root.bind("<Return>", lambda e: self._handle_return())

    def _handle_return(self):
        """Handle Return key - return to menu."""
        if self.on_back_to_menu:
            self.on_back_to_menu()

    def show(self):
        """Show the screen."""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide the screen."""
        self.frame.pack_forget()
