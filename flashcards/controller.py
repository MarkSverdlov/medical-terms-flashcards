"""Main application controller managing screens."""

import random
import tkinter as tk

from .screens import MainMenu, FlashCardApp, QuizCardApp, QuizResultsScreen, ScoreboardScreen
from .history import save_quiz_result


class App:
    """Main application managing screens."""

    def __init__(self, root: tk.Tk, cards: list[dict]):
        self.root = root
        self.cards = cards

        self.root.title("Flash Card Game - Medical Terminology")
        self.root.geometry("600x400")
        self.root.configure(bg="#2c3e50")

        # Create screens
        self.main_menu = MainMenu(self.root, self._start_simple_mode, self._start_inverted_mode, self._start_quiz_mode, self._start_scoreboard_mode)
        self.flashcard_app = None
        self.results_screen = None
        self.scoreboard_screen = None

        # Show main menu
        self.main_menu.show()

    def _prepare_mode_cards(self) -> list[dict]:
        """Prepare a shuffled deck of cards for a mode."""
        card_count = self.main_menu.get_card_count()
        mode_cards = random.choices(self.cards, k=card_count)
        random.shuffle(mode_cards)
        return mode_cards

    def _start_simple_mode(self):
        """Switch to simple mode (flashcard game)."""
        self.main_menu.hide()
        mode_cards = self._prepare_mode_cards()
        self.flashcard_app = FlashCardApp(self.root, mode_cards, self._back_to_menu, mode="simple")
        self.flashcard_app.show()

    def _start_inverted_mode(self):
        """Switch to inverted mode (flashcard game with swapped front/back)."""
        self.main_menu.hide()
        mode_cards = self._prepare_mode_cards()
        self.flashcard_app = FlashCardApp(self.root, mode_cards, self._back_to_menu, mode="inverted")
        self.flashcard_app.show()

    def _start_quiz_mode(self):
        """Switch to quiz mode (type the term for the interpretation)."""
        self.main_menu.hide()
        mode_cards = self._prepare_mode_cards()
        self.flashcard_app = QuizCardApp(
            self.root, mode_cards, self._back_to_menu, self._on_quiz_complete
        )
        self.flashcard_app.show()

    def _start_scoreboard_mode(self):
        """Switch to scoreboard screen."""
        self.main_menu.hide()
        self.scoreboard_screen = ScoreboardScreen(self.root, self._back_to_menu_from_scoreboard)
        self.scoreboard_screen.show()

    def _back_to_menu_from_scoreboard(self):
        """Return to main menu from scoreboard screen."""
        if self.scoreboard_screen:
            self.scoreboard_screen.hide()
            self.scoreboard_screen = None
        self.main_menu.show()

    def _on_quiz_complete(self, correct: int, total: int):
        """Handle quiz completion - save results and show summary."""
        save_quiz_result(total, correct)
        if self.flashcard_app:
            self.flashcard_app.hide()
            self.flashcard_app = None
        self.results_screen = QuizResultsScreen(
            self.root, correct, total, self._back_to_menu_from_results
        )
        self.results_screen.show()

    def _back_to_menu_from_results(self):
        """Return to main menu from results screen."""
        if self.results_screen:
            self.results_screen.hide()
            self.results_screen = None
        self.main_menu.show()

    def _back_to_menu(self):
        """Return to main menu."""
        if self.flashcard_app:
            self.flashcard_app.hide()
            self.flashcard_app = None
        self.main_menu.show()
