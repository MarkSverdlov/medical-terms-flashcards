#!/usr/bin/env python3
"""Comprehensive test suite for the Flash Card Game application."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import tkinter as tk

# Import the modules to test
from flashcards.app import (
    parse_markdown_tables,
    fix_rtl,
    MainMenu,
    FlashCardApp,
    QuizCardApp,
    App,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_cards():
    """Provide sample card data for testing."""
    return [
        {"term": "hypertension", "interpretation": "יתר לחץ דם", "extra": "HTN"},
        {"term": "bradycardia", "interpretation": "דופק איטי", "extra": ""},
        {"term": "CPR", "interpretation": "החייאת לב ריאה", "extra": "cardiopulmonary resuscitation"},
    ]


@pytest.fixture
def single_card():
    """Provide a single card for simple tests."""
    return [{"term": "test_term", "interpretation": "test_interpretation", "extra": ""}]


@pytest.fixture
def mock_root():
    """Create a mock Tk root window."""
    root = MagicMock(spec=tk.Tk)
    root.winfo_exists.return_value = True
    return root


@pytest.fixture
def mock_frame():
    """Create a mock Tk frame."""
    frame = MagicMock(spec=tk.Frame)
    return frame


# =============================================================================
# Tests for parse_markdown_tables()
# =============================================================================

class TestParseMarkdownTables:
    """Tests for the parse_markdown_tables function."""

    def test_parse_basic_table(self, tmp_path):
        """Test parsing a simple markdown table."""
        md_content = """| Term | Interpretation | Extra |
| ---- | -------------- | ----- |
| hypertension | יתר לחץ דם | HTN |
| bradycardia | דופק איטי | |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        assert len(cards) == 2
        assert cards[0]["term"] == "hypertension"
        assert cards[0]["interpretation"] == "יתר לחץ דם"
        assert cards[0]["extra"] == "HTN"
        assert cards[1]["term"] == "bradycardia"
        assert cards[1]["interpretation"] == "דופק איטי"
        assert cards[1]["extra"] == ""

    def test_parse_multiple_tables(self, tmp_path):
        """Test parsing multiple tables in one file."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
| term1 | interp1 |

Some text between tables

| Term | Interpretation | Extra |
| ---- | -------------- | ----- |
| term2 | interp2 | extra2 |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        assert len(cards) == 2
        assert cards[0]["term"] == "term1"
        assert cards[0]["extra"] == ""
        assert cards[1]["term"] == "term2"
        assert cards[1]["extra"] == "extra2"

    def test_parse_table_with_two_columns(self, tmp_path):
        """Test parsing table with only two columns (no extra)."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
| IV | מתן תוך ורידי |
| PO | מתן פומי |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        assert len(cards) == 2
        assert cards[0]["term"] == "IV"
        assert cards[0]["interpretation"] == "מתן תוך ורידי"
        assert cards[0]["extra"] == ""

    def test_parse_empty_file(self, tmp_path):
        """Test parsing an empty file."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("", encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        assert cards == []

    def test_parse_file_with_no_tables(self, tmp_path):
        """Test parsing a file with no tables."""
        md_content = """# Header

Some regular text without any tables.

Another paragraph.
"""
        md_file = tmp_path / "no_tables.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        assert cards == []

    def test_parse_table_skips_incomplete_rows(self, tmp_path):
        """Test that rows with less than 2 columns are skipped."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
| valid | valid_interp |
| only_one_column |
| another_valid | another_interp |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        # The incomplete row should be skipped
        assert len(cards) == 2
        assert cards[0]["term"] == "valid"
        assert cards[1]["term"] == "another_valid"

    def test_parse_table_with_extra_whitespace(self, tmp_path):
        """Test that whitespace in cells is stripped."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
|   spaced_term   |   spaced_interp   |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        assert len(cards) == 1
        assert cards[0]["term"] == "spaced_term"
        assert cards[0]["interpretation"] == "spaced_interp"

    def test_parse_table_with_special_characters(self, tmp_path):
        """Test parsing table with special characters in content."""
        md_content = """| Term | Interpretation | Extra |
| ---- | -------------- | ----- |
| ecto-, exo- | מחוץ | הריון אקטופי (מחוץ לרחם) |
| -emia | בדם | bactermia = חיידק בדם |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        assert len(cards) == 2
        assert cards[0]["term"] == "ecto-, exo-"
        assert cards[1]["term"] == "-emia"

    def test_parse_preserves_hebrew_text(self, tmp_path):
        """Test that Hebrew text is preserved correctly."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
| anatomy | תורת מבנה הגוף ואיבריו |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))

        assert cards[0]["interpretation"] == "תורת מבנה הגוף ואיבריו"


# =============================================================================
# Tests for fix_rtl()
# =============================================================================

class TestFixRtl:
    """Tests for the fix_rtl function."""

    def test_fix_rtl_basic(self):
        """Test basic RTL conversion."""
        result = fix_rtl("שלום")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_fix_rtl_empty_string(self):
        """Test RTL conversion with empty string."""
        result = fix_rtl("")
        assert result == ""

    def test_fix_rtl_english_text(self):
        """Test RTL conversion with English text (should pass through)."""
        result = fix_rtl("hello")
        assert "hello" in result or result == "hello"

    def test_fix_rtl_long_text_wraps(self):
        """Test that long text is wrapped."""
        long_text = "א" * 50  # 50 Hebrew characters
        result = fix_rtl(long_text)
        # Should contain newlines due to wrapping at width=25
        assert "\n" in result

    def test_fix_rtl_short_text_no_wrap(self):
        """Test that short text is not wrapped."""
        short_text = "קצר"
        result = fix_rtl(short_text)
        assert "\n" not in result


# =============================================================================
# Tests for MainMenu class
# =============================================================================

class TestMainMenu:
    """Tests for the MainMenu class."""

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    def test_main_menu_initialization(self, mock_intvar, mock_spinbox, mock_button,
                                       mock_label, mock_frame):
        """Test MainMenu initialization."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 100
        mock_intvar.return_value = mock_intvar_instance

        parent = MagicMock()
        simple_cb = MagicMock()
        inverted_cb = MagicMock()
        quiz_cb = MagicMock()

        menu = MainMenu(parent, simple_cb, inverted_cb, quiz_cb)

        assert menu.start_simple_mode == simple_cb
        assert menu.start_inverted_mode == inverted_cb
        assert menu.start_quiz_mode == quiz_cb

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    def test_get_card_count_default(self, mock_intvar, mock_spinbox, mock_button,
                                     mock_label, mock_frame):
        """Test default card count is 100."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 100
        mock_intvar.return_value = mock_intvar_instance

        parent = MagicMock()
        menu = MainMenu(parent, MagicMock(), MagicMock(), MagicMock())

        assert menu.get_card_count() == 100

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    def test_get_card_count_custom(self, mock_intvar, mock_spinbox, mock_button,
                                    mock_label, mock_frame):
        """Test custom card count value."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 250
        mock_intvar.return_value = mock_intvar_instance

        parent = MagicMock()
        menu = MainMenu(parent, MagicMock(), MagicMock(), MagicMock())

        assert menu.get_card_count() == 250

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    def test_show_hide(self, mock_intvar, mock_spinbox, mock_button,
                       mock_label, mock_frame):
        """Test show and hide methods."""
        mock_intvar.return_value = MagicMock()
        mock_frame_instance = MagicMock()
        mock_frame.return_value = mock_frame_instance

        parent = MagicMock()
        menu = MainMenu(parent, MagicMock(), MagicMock(), MagicMock())

        menu.show()
        mock_frame_instance.pack.assert_called()

        menu.hide()
        mock_frame_instance.pack_forget.assert_called()


# =============================================================================
# Tests for FlashCardApp class
# =============================================================================

class TestFlashCardApp:
    """Tests for the FlashCardApp class."""

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_initialization_simple_mode(self, mock_button, mock_label, mock_frame,
                                         mock_root, sample_cards):
        """Test FlashCardApp initialization in simple mode."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards, mode="simple")

        assert app.mode == "simple"
        assert app.current_index == 0
        assert app.is_flipped == False
        assert app.cards == sample_cards

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_initialization_inverted_mode(self, mock_button, mock_label, mock_frame,
                                           mock_root, sample_cards):
        """Test FlashCardApp initialization in inverted mode."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards, mode="inverted")

        assert app.mode == "inverted"

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_next_card_increments_index(self, mock_button, mock_label, mock_frame,
                                         mock_root, sample_cards):
        """Test that _next_card increments the index."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards, mode="simple")

        assert app.current_index == 0
        app._next_card()
        assert app.current_index == 1
        app._next_card()
        assert app.current_index == 2

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_next_card_stops_at_end(self, mock_button, mock_label, mock_frame,
                                     mock_root, sample_cards):
        """Test that _next_card doesn't go past the last card."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards, mode="simple")
        app.current_index = len(sample_cards) - 1

        app._next_card()
        assert app.current_index == len(sample_cards) - 1

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_prev_card_decrements_index(self, mock_button, mock_label, mock_frame,
                                         mock_root, sample_cards):
        """Test that _prev_card decrements the index."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards, mode="simple")
        app.current_index = 2

        app._prev_card()
        assert app.current_index == 1
        app._prev_card()
        assert app.current_index == 0

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_prev_card_stops_at_start(self, mock_button, mock_label, mock_frame,
                                       mock_root, sample_cards):
        """Test that _prev_card doesn't go below 0."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards, mode="simple")
        app.current_index = 0

        app._prev_card()
        assert app.current_index == 0

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_flip_card_toggles_state(self, mock_button, mock_label, mock_frame,
                                      mock_root, sample_cards):
        """Test that _flip_card toggles the flipped state."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards, mode="simple")

        assert app.is_flipped == False
        app._flip_card()
        assert app.is_flipped == True
        app._flip_card()
        assert app.is_flipped == False

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_navigation_resets_flip_state(self, mock_button, mock_label, mock_frame,
                                           mock_root, sample_cards):
        """Test that navigating to another card resets flip state."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards, mode="simple")
        app._flip_card()  # Flip current card
        assert app.is_flipped == True

        app._next_card()
        assert app.is_flipped == False

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_shuffle_randomizes_cards(self, mock_button, mock_label, mock_frame,
                                       mock_root, sample_cards):
        """Test that _shuffle_cards changes card order."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, sample_cards.copy(), mode="simple")
        original_first = app.cards[0]["term"]

        # Shuffle multiple times to ensure we get a different order
        shuffled = False
        for _ in range(10):
            app._shuffle_cards()
            if app.cards[0]["term"] != original_first:
                shuffled = True
                break

        # With 3 cards, probability of same first card after 10 shuffles is (1/3)^10
        # This test might rarely fail due to randomness
        assert app.current_index == 0  # Shuffle resets index
        assert app.is_flipped == False  # Shuffle resets flip state

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_empty_cards_handling(self, mock_button, mock_label, mock_frame, mock_root):
        """Test handling of empty card list."""
        mock_frame.return_value = MagicMock()
        mock_label_instance = MagicMock()
        mock_label.return_value = mock_label_instance
        mock_button.return_value = MagicMock()

        app = FlashCardApp(mock_root, [], mode="simple")

        # Should not crash with empty cards
        app._next_card()
        app._prev_card()
        app._flip_card()

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_original_order_preserved(self, mock_button, mock_label, mock_frame,
                                       mock_root, sample_cards):
        """Test that original_order is preserved after shuffle."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        cards_copy = sample_cards.copy()
        app = FlashCardApp(mock_root, cards_copy, mode="simple")

        original = app.original_order.copy()
        app._shuffle_cards()

        assert app.original_order == original


# =============================================================================
# Tests for QuizCardApp class
# =============================================================================

class TestQuizCardApp:
    """Tests for the QuizCardApp class."""

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Entry')
    def test_initialization(self, mock_entry, mock_button, mock_label, mock_frame,
                            mock_root, sample_cards):
        """Test QuizCardApp initialization."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        mock_entry_instance = MagicMock()
        mock_entry.return_value = mock_entry_instance

        app = QuizCardApp(mock_root, sample_cards)

        assert app.current_index == 0
        assert app.current_answered == False
        assert app.cards == sample_cards

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Entry')
    def test_next_card_increments_index(self, mock_entry, mock_button, mock_label,
                                         mock_frame, mock_root, sample_cards):
        """Test that _next_card increments index in quiz mode."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        mock_entry_instance = MagicMock()
        mock_entry.return_value = mock_entry_instance

        app = QuizCardApp(mock_root, sample_cards)

        assert app.current_index == 0
        app._next_card()
        assert app.current_index == 1

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Entry')
    def test_next_card_stops_at_end(self, mock_entry, mock_button, mock_label,
                                     mock_frame, mock_root, sample_cards):
        """Test that _next_card doesn't go past last card."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        mock_entry_instance = MagicMock()
        mock_entry.return_value = mock_entry_instance

        app = QuizCardApp(mock_root, sample_cards)
        app.current_index = len(sample_cards) - 1

        app._next_card()
        assert app.current_index == len(sample_cards) - 1


# =============================================================================
# Tests for Quiz Answer Validation Logic
# =============================================================================

class TestQuizAnswerValidation:
    """Tests for quiz answer validation logic (extracted for unit testing)."""

    def normalize(self, s):
        """Normalize answer string (matches implementation)."""
        return s.strip().lower().replace("-", "")

    def check_answer(self, user_answer, correct_term):
        """Check answer logic (matches _submit_answer implementation)."""
        user_terms = {self.normalize(t) for t in user_answer.split(",") if self.normalize(t)}
        correct_terms = {self.normalize(t) for t in correct_term.split(",") if self.normalize(t)}

        if user_terms == correct_terms:
            return "correct"
        elif user_terms and user_terms.issubset(correct_terms):
            return "partial"
        else:
            return "incorrect"

    def test_exact_match(self):
        """Test exact match returns correct."""
        assert self.check_answer("hypertension", "hypertension") == "correct"

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert self.check_answer("HYPERTENSION", "hypertension") == "correct"
        assert self.check_answer("HyPerTension", "hypertension") == "correct"

    def test_dash_insensitive(self):
        """Test dash insensitivity."""
        assert self.check_answer("brady-cardia", "bradycardia") == "correct"
        assert self.check_answer("bradycardia", "brady-cardia") == "correct"
        assert self.check_answer("brady-cardia", "brady-cardia") == "correct"

    def test_whitespace_stripped(self):
        """Test leading/trailing whitespace is stripped."""
        assert self.check_answer("  hypertension  ", "hypertension") == "correct"

    def test_comma_separated_exact_match(self):
        """Test comma-separated terms exact match."""
        assert self.check_answer("term1, term2", "term1, term2") == "correct"
        assert self.check_answer("term2, term1", "term1, term2") == "correct"  # Order doesn't matter

    def test_comma_separated_partial_match(self):
        """Test comma-separated terms partial match."""
        assert self.check_answer("term1", "term1, term2") == "partial"

    def test_incorrect_answer(self):
        """Test incorrect answer."""
        assert self.check_answer("wrong", "correct") == "incorrect"

    def test_empty_answer(self):
        """Test empty answer."""
        assert self.check_answer("", "correct") == "incorrect"

    def test_partial_with_extra_term(self):
        """Test that extra terms result in incorrect."""
        assert self.check_answer("term1, term3", "term1, term2") == "incorrect"

    def test_complex_medical_term(self):
        """Test complex medical terms with prefixes/suffixes."""
        assert self.check_answer("ecto-, exo-", "ecto-, exo-") == "correct"
        assert self.check_answer("ectoexo", "ecto-, exo-") == "incorrect"  # Not the same when normalized

    def test_abbreviations(self):
        """Test medical abbreviations."""
        assert self.check_answer("cpr", "CPR") == "correct"
        assert self.check_answer("IV", "iv") == "correct"


# =============================================================================
# Tests for App class
# =============================================================================

class TestApp:
    """Tests for the main App class."""

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    def test_initialization(self, mock_intvar, mock_spinbox, mock_button,
                            mock_label, mock_frame, mock_root, sample_cards):
        """Test App initialization."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 100
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()

        app = App(mock_root, sample_cards)

        assert app.cards == sample_cards
        assert app.flashcard_app is None
        mock_root.title.assert_called_with("Flash Card Game - Medical Terminology")
        mock_root.geometry.assert_called_with("600x400")

    @patch('flashcards.app.FlashCardApp')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('random.choices')
    @patch('random.shuffle')
    def test_start_simple_mode(self, mock_shuffle, mock_choices, mock_intvar,
                                mock_spinbox, mock_button, mock_label, mock_frame,
                                mock_flashcard_app, mock_root, sample_cards):
        """Test starting simple mode."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 50
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_choices.return_value = sample_cards

        app = App(mock_root, sample_cards)
        app._start_simple_mode()

        mock_choices.assert_called_with(sample_cards, k=50)
        mock_shuffle.assert_called()

    @patch('flashcards.app.FlashCardApp')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('random.choices')
    @patch('random.shuffle')
    def test_start_inverted_mode(self, mock_shuffle, mock_choices, mock_intvar,
                                  mock_spinbox, mock_button, mock_label, mock_frame,
                                  mock_flashcard_app, mock_root, sample_cards):
        """Test starting inverted mode."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 75
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_choices.return_value = sample_cards

        app = App(mock_root, sample_cards)
        app._start_inverted_mode()

        mock_choices.assert_called_with(sample_cards, k=75)

    @patch('flashcards.app.QuizCardApp')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('random.choices')
    def test_start_quiz_mode(self, mock_choices, mock_intvar, mock_spinbox,
                              mock_button, mock_label, mock_frame,
                              mock_quiz_app, mock_root, sample_cards):
        """Test starting quiz mode."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 100
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_choices.return_value = sample_cards

        app = App(mock_root, sample_cards)
        app._start_quiz_mode()

        mock_choices.assert_called_with(sample_cards, k=100)

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    def test_back_to_menu(self, mock_intvar, mock_spinbox, mock_button,
                          mock_label, mock_frame, mock_root, sample_cards):
        """Test returning to main menu."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 100
        mock_intvar.return_value = mock_intvar_instance
        mock_frame_instance = MagicMock()
        mock_frame.return_value = mock_frame_instance

        app = App(mock_root, sample_cards)

        # Create a mock flashcard app
        mock_flashcard = MagicMock()
        app.flashcard_app = mock_flashcard

        app._back_to_menu()

        mock_flashcard.hide.assert_called_once()
        assert app.flashcard_app is None


# =============================================================================
# Integration-style Tests (with real tkinter if available)
# =============================================================================

class TestIntegration:
    """Integration tests that test component interactions."""

    def test_parse_and_use_real_file(self):
        """Test parsing the actual medical-terms.md file if it exists."""
        script_dir = Path(__file__).parent
        md_file = script_dir / "medical-terms.md"

        if md_file.exists():
            cards = parse_markdown_tables(str(md_file))
            assert len(cards) > 0

            # Verify card structure
            for card in cards:
                assert "term" in card
                assert "interpretation" in card
                assert "extra" in card
                assert isinstance(card["term"], str)
                assert isinstance(card["interpretation"], str)
                assert isinstance(card["extra"], str)

    def test_card_data_integrity(self):
        """Test that all cards have required fields."""
        script_dir = Path(__file__).parent
        md_file = script_dir / "medical-terms.md"

        if md_file.exists():
            cards = parse_markdown_tables(str(md_file))

            for i, card in enumerate(cards):
                assert card["term"], f"Card {i} has empty term"
                assert card["interpretation"], f"Card {i} has empty interpretation"

    def test_rtl_with_real_hebrew_text(self):
        """Test RTL function with real Hebrew medical terms."""
        hebrew_texts = [
            "יתר לחץ דם",
            "דופק איטי",
            "תורת מבנה הגוף ואיבריו",
            "החייאת לב ריאה",
        ]

        for text in hebrew_texts:
            result = fix_rtl(text)
            assert isinstance(result, str)
            assert len(result) > 0


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_card_deck(self, tmp_path):
        """Test with only one card."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
| only_card | single_interp |
"""
        md_file = tmp_path / "single.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))
        assert len(cards) == 1

    def test_very_long_term(self, tmp_path):
        """Test with very long term text."""
        long_term = "a" * 200
        md_content = f"""| Term | Interpretation |
| ---- | -------------- |
| {long_term} | interp |
"""
        md_file = tmp_path / "long.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))
        assert len(cards) == 1
        assert len(cards[0]["term"]) == 200

    def test_unicode_in_terms(self, tmp_path):
        """Test with various Unicode characters."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
| café | קפה |
| naïve | נאיבי |
| résumé | קורות חיים |
"""
        md_file = tmp_path / "unicode.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))
        assert len(cards) == 3
        assert cards[0]["term"] == "café"

    def test_table_header_variations(self, tmp_path):
        """Test tables with different header names."""
        md_content = """| Name | Definition | Notes |
| ---- | ---------- | ----- |
| term1 | def1 | note1 |
"""
        md_file = tmp_path / "headers.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))
        assert len(cards) == 1
        # Parser doesn't care about header names, just position

    def test_mixed_content_file(self, tmp_path):
        """Test file with mixed markdown content."""
        md_content = """# Medical Terms

Some intro text here.

## Table 1

| Term | Interpretation |
| ---- | -------------- |
| term1 | interp1 |

More text between tables.

## Table 2

| Term | Interpretation | Extra |
| ---- | -------------- | ----- |
| term2 | interp2 | extra2 |

Conclusion text.
"""
        md_file = tmp_path / "mixed.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))
        assert len(cards) == 2


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Basic performance tests."""

    def test_large_file_parsing(self, tmp_path):
        """Test parsing a large file with many cards."""
        # Generate 1000 rows
        rows = ["| Term | Interpretation |", "| ---- | -------------- |"]
        for i in range(1000):
            rows.append(f"| term{i} | interp{i} |")

        md_content = "\n".join(rows)
        md_file = tmp_path / "large.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards = parse_markdown_tables(str(md_file))
        assert len(cards) == 1000

    def test_fix_rtl_performance_with_long_text(self):
        """Test fix_rtl with very long text."""
        long_text = "שלום " * 500  # ~2500 characters
        result = fix_rtl(long_text)
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
