"""Main menu screen for the flash card application."""

import tkinter as tk

from ..utils import fix_rtl


class MainMenu:
    """Main menu screen."""

    def __init__(self, parent: tk.Frame, start_simple_mode: callable, start_inverted_mode: callable, start_quiz_mode: callable, start_scoreboard_mode: callable, section_counts: dict[str, int] = None):
        self.frame = tk.Frame(parent, bg="#2c3e50")
        self.start_simple_mode = start_simple_mode
        self.start_inverted_mode = start_inverted_mode
        self.start_quiz_mode = start_quiz_mode
        self.start_scoreboard_mode = start_scoreboard_mode
        self.section_counts = section_counts or {}
        self.section_vars: dict[str, tk.BooleanVar] = {}
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
        title_label.pack(pady=(10, 2))

        # Subtitle
        subtitle_label = tk.Label(
            self.frame,
            text="Medical Terminology",
            font=("Helvetica", 16),
            fg="#bdc3c7",
            bg="#2c3e50",
        )
        subtitle_label.pack(pady=(0, 5))

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

        # Sections label
        if self.section_counts:
            sections_label = tk.Label(
                self.frame,
                text="Sections:",
                font=("Helvetica", 12),
                fg="white",
                bg="#2c3e50",
            )
            sections_label.pack(pady=(5, 2))

            # Check All / Uncheck All buttons
            btn_frame = tk.Frame(self.frame, bg="#2c3e50")
            btn_frame.pack(pady=2)

            tk.Button(
                btn_frame,
                text="Check All",
                font=("Helvetica", 10),
                command=self._check_all,
                width=10,
            ).pack(side="left", padx=5)

            tk.Button(
                btn_frame,
                text="Uncheck All",
                font=("Helvetica", 10),
                command=self._uncheck_all,
                width=10,
            ).pack(side="left", padx=5)

            # Scrollable frame for section checkboxes
            canvas_frame = tk.Frame(self.frame, bg="#2c3e50")
            canvas_frame.pack(pady=2, padx=20)

            self.canvas = tk.Canvas(canvas_frame, bg="#2c3e50", height=70, width=260, highlightthickness=0)
            scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
            scrollable_frame = tk.Frame(self.canvas, bg="#2c3e50")

            scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            )

            self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            self.canvas.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side="left", fill="y")
            self.canvas.pack(side="left", fill=tk.BOTH, expand=True)

            # Bind keyboard events for scrolling
            self.frame.bind("<Down>", self._scroll_down)
            self.frame.bind("<Up>", self._scroll_up)
            self.frame.bind("<Control-d>", self._scroll_to_bottom)
            self.frame.bind("<Control-u>", self._scroll_to_top)

            # Create checkbox for each section
            for section, count in self.section_counts.items():
                var = tk.BooleanVar(value=True)
                self.section_vars[section] = var
                cb = tk.Checkbutton(
                    scrollable_frame,
                    text=fix_rtl(f"{section} - {count} terms", wrap_width=None),
                    variable=var,
                    font=("Helvetica", 10),
                    fg="white",
                    bg="#2c3e50",
                    selectcolor="#34495e",
                    activebackground="#2c3e50",
                    activeforeground="white",
                    anchor="w",
                )
                cb.pack(fill=tk.X, anchor="w")

        # Mode buttons in 2x2 grid
        buttons_frame = tk.Frame(self.frame, bg="#2c3e50")
        buttons_frame.pack(pady=5)

        simple_mode_btn = tk.Button(
            buttons_frame,
            text="Simple Mode",
            font=("Helvetica", 14),
            command=self.start_simple_mode,
            width=12,
        )
        simple_mode_btn.grid(row=0, column=0, padx=5, pady=3)

        inverted_mode_btn = tk.Button(
            buttons_frame,
            text="Inverted Mode",
            font=("Helvetica", 14),
            command=self.start_inverted_mode,
            width=12,
        )
        inverted_mode_btn.grid(row=0, column=1, padx=5, pady=3)

        quiz_mode_btn = tk.Button(
            buttons_frame,
            text="Quiz Mode",
            font=("Helvetica", 14),
            command=self.start_quiz_mode,
            width=12,
        )
        quiz_mode_btn.grid(row=1, column=0, padx=5, pady=3)

        scoreboard_btn = tk.Button(
            buttons_frame,
            text="Scoreboard",
            font=("Helvetica", 14),
            command=self.start_scoreboard_mode,
            width=12,
        )
        scoreboard_btn.grid(row=1, column=1, padx=5, pady=3)

    def get_card_count(self) -> int:
        """Return the selected number of cards."""
        return self.card_count_var.get()

    def _check_all(self):
        """Set all section checkboxes to True."""
        for var in self.section_vars.values():
            var.set(True)

    def _uncheck_all(self):
        """Set all section checkboxes to False."""
        for var in self.section_vars.values():
            var.set(False)

    def _scroll_down(self, event=None):
        """Scroll the sections list down."""
        if hasattr(self, 'canvas'):
            self.canvas.yview_scroll(1, "units")

    def _scroll_up(self, event=None):
        """Scroll the sections list up."""
        if hasattr(self, 'canvas'):
            self.canvas.yview_scroll(-1, "units")

    def _scroll_to_bottom(self, event=None):
        """Scroll the sections list to the bottom."""
        if hasattr(self, 'canvas'):
            self.canvas.yview_moveto(1.0)

    def _scroll_to_top(self, event=None):
        """Scroll the sections list to the top."""
        if hasattr(self, 'canvas'):
            self.canvas.yview_moveto(0.0)

    def get_selected_sections(self) -> set[str]:
        """Return the set of selected section names."""
        return {section for section, var in self.section_vars.items() if var.get()}

    def show(self):
        """Show the main menu."""
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.focus_set()

    def hide(self):
        """Hide the main menu."""
        self.frame.pack_forget()
