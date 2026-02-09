"""Scoreboard screen displaying quiz history."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ..history import load_quiz_history


class ScoreboardScreen:
    """Screen showing quiz history in a scrollable table."""

    def __init__(self, parent: tk.Frame, back_to_menu: callable):
        self.frame = tk.Frame(parent, bg="#2c3e50")
        self.back_to_menu = back_to_menu
        self._setup_ui()

    def _setup_ui(self):
        """Set up the scoreboard UI."""
        # Header frame
        header_frame = tk.Frame(self.frame, bg="#2c3e50")
        header_frame.pack(fill=tk.X, pady=(10, 5))

        # Back button
        back_btn = tk.Button(
            header_frame,
            text="← Back",
            font=("Helvetica", 12),
            command=self.back_to_menu,
        )
        back_btn.pack(side="left", padx=10)

        # Title
        title_label = tk.Label(
            header_frame,
            text="Scoreboard",
            font=("Helvetica", 24, "bold"),
            fg="white",
            bg="#2c3e50",
        )
        title_label.pack(side="left", expand=True)

        # Spacer to balance the back button
        spacer = tk.Frame(header_frame, width=80, bg="#2c3e50")
        spacer.pack(side="right")

        # Load history
        history = load_quiz_history()

        if not history:
            # Empty state
            empty_label = tk.Label(
                self.frame,
                text="No quiz history yet",
                font=("Helvetica", 16),
                fg="#bdc3c7",
                bg="#2c3e50",
            )
            empty_label.pack(expand=True)
        else:
            # Table container
            table_frame = tk.Frame(self.frame, bg="#2c3e50")
            table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Configure treeview style
            style = ttk.Style()
            style.configure(
                "Scoreboard.Treeview",
                background="#34495e",
                foreground="white",
                fieldbackground="#34495e",
                rowheight=25,
            )
            style.configure(
                "Scoreboard.Treeview.Heading",
                background="#2c3e50",
                foreground="black",
                font=("Helvetica", 11, "bold"),
            )

            # Create treeview with columns
            columns = ("datetime", "questions", "correct", "percentage")
            self.tree = ttk.Treeview(
                table_frame,
                columns=columns,
                show="headings",
                style="Scoreboard.Treeview",
            )

            # Define headings
            self.tree.heading("datetime", text="Date/Time")
            self.tree.heading("questions", text="Questions")
            self.tree.heading("correct", text="Correct")
            self.tree.heading("percentage", text="Percentage")

            # Define column widths
            self.tree.column("datetime", width=150, anchor="center")
            self.tree.column("questions", width=80, anchor="center")
            self.tree.column("correct", width=80, anchor="center")
            self.tree.column("percentage", width=80, anchor="center")

            # Add scrollbar
            scrollbar = ttk.Scrollbar(
                table_frame, orient=tk.VERTICAL, command=self.tree.yview
            )
            self.tree.configure(yscrollcommand=scrollbar.set)

            # Pack tree and scrollbar
            self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Populate table (most recent first)
            for entry in reversed(history):
                dt = datetime.fromisoformat(entry["time"])
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                total = entry["total"]
                correct = entry["correct"]
                percentage = f"{(correct / total * 100):.0f}%" if total > 0 else "0%"

                self.tree.insert(
                    "", tk.END, values=(formatted_time, total, correct, percentage)
                )

    def show(self):
        """Show the scoreboard screen."""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide the scoreboard screen."""
        self.frame.pack_forget()
