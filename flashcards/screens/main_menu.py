"""Main menu screen for the flash card application."""

import tkinter as tk


class MainMenu:
    """Main menu screen."""

    def __init__(self, parent: tk.Frame, start_simple_mode: callable, start_inverted_mode: callable, start_quiz_mode: callable):
        self.frame = tk.Frame(parent, bg="#2c3e50")
        self.start_simple_mode = start_simple_mode
        self.start_inverted_mode = start_inverted_mode
        self.start_quiz_mode = start_quiz_mode
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
        title_label.pack(pady=(20, 5))

        # Subtitle
        subtitle_label = tk.Label(
            self.frame,
            text="Medical Terminology",
            font=("Helvetica", 16),
            fg="#bdc3c7",
            bg="#2c3e50",
        )
        subtitle_label.pack(pady=(0, 10))

        # Card count configuration
        config_frame = tk.Frame(self.frame, bg="#2c3e50")
        config_frame.pack(pady=10)

        tk.Label(
            config_frame,
            text="Number of cards:",
            font=("Helvetica", 12),
            fg="white",
            bg="#2c3e50",
        ).pack(side="left")

        self.card_count_var = tk.IntVar(value=100)
        self.card_count_spinbox = tk.Spinbox(
            config_frame,
            from_=10,
            to=500,
            textvariable=self.card_count_var,
            width=5,
            font=("Helvetica", 12),
        )
        self.card_count_spinbox.pack(side="left", padx=10)

        # Simple Mode button
        simple_mode_btn = tk.Button(
            self.frame,
            text="Simple Mode",
            font=("Helvetica", 14),
            command=self.start_simple_mode,
            width=15,
        )
        simple_mode_btn.pack(pady=5)

        # Inverted Mode button
        inverted_mode_btn = tk.Button(
            self.frame,
            text="Inverted Mode",
            font=("Helvetica", 14),
            command=self.start_inverted_mode,
            width=15,
        )
        inverted_mode_btn.pack(pady=5)

        # Quiz Mode button
        quiz_mode_btn = tk.Button(
            self.frame,
            text="Quiz Mode",
            font=("Helvetica", 14),
            command=self.start_quiz_mode,
            width=15,
        )
        quiz_mode_btn.pack(pady=5)

    def get_card_count(self) -> int:
        """Return the selected number of cards."""
        return self.card_count_var.get()

    def show(self):
        """Show the main menu."""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide the main menu."""
        self.frame.pack_forget()
