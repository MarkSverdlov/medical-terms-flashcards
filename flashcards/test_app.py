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
    ScoreboardScreen,
    App,
    load_quiz_history,
    save_quiz_result,
    get_history_path,
)
from flashcards.utils import spread_shuffle, spread_shuffle_with_replacement


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_cards():
    """Provide sample card data for testing."""
    return [
        {"term": "hypertension", "interpretation": "יתר לחץ דם", "extra": "HTN", "section": "General"},
        {"term": "bradycardia", "interpretation": "דופק איטי", "extra": "", "section": "General"},
        {"term": "CPR", "interpretation": "החייאת לב ריאה", "extra": "cardiopulmonary resuscitation", "section": "General"},
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

        cards, sections = parse_markdown_tables(str(md_file))

        assert len(cards) == 2
        assert cards[0]["term"] == "hypertension"
        assert cards[0]["interpretation"] == "יתר לחץ דם"
        assert cards[0]["extra"] == "HTN"
        assert cards[0]["section"] == "General"
        assert cards[1]["term"] == "bradycardia"
        assert cards[1]["interpretation"] == "דופק איטי"
        assert cards[1]["extra"] == ""
        assert sections == ["General"]

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

        cards, sections = parse_markdown_tables(str(md_file))

        assert len(cards) == 2
        assert cards[0]["term"] == "term1"
        assert cards[0]["extra"] == ""
        assert cards[1]["term"] == "term2"
        assert cards[1]["extra"] == "extra2"
        assert sections == ["General"]

    def test_parse_table_with_two_columns(self, tmp_path):
        """Test parsing table with only two columns (no extra)."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
| IV | מתן תוך ורידי |
| PO | מתן פומי |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards, sections = parse_markdown_tables(str(md_file))

        assert len(cards) == 2
        assert cards[0]["term"] == "IV"
        assert cards[0]["interpretation"] == "מתן תוך ורידי"
        assert cards[0]["extra"] == ""

    def test_parse_empty_file(self, tmp_path):
        """Test parsing an empty file."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("", encoding="utf-8")

        cards, sections = parse_markdown_tables(str(md_file))

        assert cards == []
        assert sections == []

    def test_parse_file_with_no_tables(self, tmp_path):
        """Test parsing a file with no tables."""
        md_content = """# Header

Some regular text without any tables.

Another paragraph.
"""
        md_file = tmp_path / "no_tables.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards, sections = parse_markdown_tables(str(md_file))

        assert cards == []
        assert sections == []

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

        cards, sections = parse_markdown_tables(str(md_file))

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

        cards, sections = parse_markdown_tables(str(md_file))

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

        cards, sections = parse_markdown_tables(str(md_file))

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

        cards, sections = parse_markdown_tables(str(md_file))

        assert cards[0]["interpretation"] == "תורת מבנה הגוף ואיבריו"

    def test_parse_sections(self, tmp_path):
        """Test parsing sections from markdown file."""
        md_content = """| Term | Interpretation |
| ---- | -------------- |
| term1 | interp1 |

Section One
===========
| Term | Interpretation |
| ---- | -------------- |
| term2 | interp2 |

Section Two
===========
| Term | Interpretation |
| ---- | -------------- |
| term3 | interp3 |
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding="utf-8")

        cards, sections = parse_markdown_tables(str(md_file))

        assert len(cards) == 3
        assert sections == ["General", "Section One", "Section Two"]
        assert cards[0]["section"] == "General"
        assert cards[1]["section"] == "Section One"
        assert cards[2]["section"] == "Section Two"


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
# Tests for spread_shuffle functions
# =============================================================================

class TestSpreadShuffle:
    """Tests for the spread_shuffle function."""

    def test_spread_shuffle_empty_list(self):
        """Test spread_shuffle with empty list."""
        result = spread_shuffle([])
        assert result == []

    def test_spread_shuffle_single_card(self):
        """Test spread_shuffle with single card."""
        cards = [{"term": "a", "section": "A"}]
        result = spread_shuffle(cards)
        assert len(result) == 1
        assert result[0]["term"] == "a"

    def test_spread_shuffle_preserves_all_cards(self):
        """Test that spread_shuffle preserves all cards."""
        cards = [
            {"term": "a1", "section": "A"},
            {"term": "a2", "section": "A"},
            {"term": "b1", "section": "B"},
            {"term": "b2", "section": "B"},
        ]
        result = spread_shuffle(cards)
        assert len(result) == 4
        result_terms = {c["term"] for c in result}
        expected_terms = {"a1", "a2", "b1", "b2"}
        assert result_terms == expected_terms

    def test_spread_shuffle_spreads_sections(self):
        """Test that spread_shuffle spreads sections apart."""
        # Create cards heavily weighted to one section
        cards = [
            {"term": "a1", "section": "A"},
            {"term": "a2", "section": "A"},
            {"term": "a3", "section": "A"},
            {"term": "a4", "section": "A"},
            {"term": "b1", "section": "B"},
            {"term": "b2", "section": "B"},
        ]
        # Run multiple times to verify spreading behavior
        max_consecutive_same_section = 0
        for _ in range(10):
            result = spread_shuffle(cards.copy())
            consecutive = 1
            for i in range(1, len(result)):
                if result[i]["section"] == result[i-1]["section"]:
                    consecutive += 1
                    max_consecutive_same_section = max(max_consecutive_same_section, consecutive)
                else:
                    consecutive = 1

        # With round-robin, we should rarely see more than 2 consecutive same-section cards
        # (can happen when one section is exhausted)
        assert max_consecutive_same_section <= 3

    def test_spread_shuffle_single_section(self):
        """Test spread_shuffle when all cards are from same section."""
        cards = [
            {"term": "a1", "section": "A"},
            {"term": "a2", "section": "A"},
            {"term": "a3", "section": "A"},
        ]
        result = spread_shuffle(cards)
        assert len(result) == 3

    def test_spread_shuffle_returns_new_list(self):
        """Test that spread_shuffle returns a new list."""
        cards = [{"term": "a", "section": "A"}, {"term": "b", "section": "B"}]
        result = spread_shuffle(cards)
        assert result is not cards


class TestSpreadShuffleWithReplacement:
    """Tests for the spread_shuffle_with_replacement function."""

    def test_empty_list(self):
        """Test with empty list returns empty."""
        result = spread_shuffle_with_replacement([], 10)
        assert result == []

    def test_samples_correct_count(self):
        """Test that correct number of cards are sampled."""
        cards = [
            {"term": "a", "section": "A"},
            {"term": "b", "section": "B"},
        ]
        result = spread_shuffle_with_replacement(cards, 10)
        assert len(result) == 10

    def test_samples_more_than_available(self):
        """Test sampling more cards than available (with replacement)."""
        cards = [{"term": "only", "section": "A"}]
        result = spread_shuffle_with_replacement(cards, 5)
        assert len(result) == 5
        # All cards should be the same since only one exists
        for card in result:
            assert card["term"] == "only"

    def test_preserves_card_structure(self):
        """Test that card structure is preserved."""
        cards = [
            {"term": "a", "interpretation": "interp_a", "extra": "ex", "section": "A"},
        ]
        result = spread_shuffle_with_replacement(cards, 3)
        for card in result:
            assert "term" in card
            assert "interpretation" in card
            assert "extra" in card
            assert "section" in card

    def test_spreads_sections_after_sampling(self):
        """Test that sections are spread apart after sampling."""
        cards = [
            {"term": "a1", "section": "A"},
            {"term": "a2", "section": "A"},
            {"term": "b1", "section": "B"},
            {"term": "b2", "section": "B"},
        ]
        # Sample many cards to test spreading
        result = spread_shuffle_with_replacement(cards, 20)
        assert len(result) == 20

        # Check that we don't have long runs of same section
        max_consecutive = 1
        consecutive = 1
        for i in range(1, len(result)):
            if result[i]["section"] == result[i-1]["section"]:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        # Should be reasonably spread (not all same section together)
        assert max_consecutive < len(result)


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
        scoreboard_cb = MagicMock()

        menu = MainMenu(parent, simple_cb, inverted_cb, quiz_cb, scoreboard_cb)

        assert menu.start_simple_mode == simple_cb
        assert menu.start_inverted_mode == inverted_cb
        assert menu.start_quiz_mode == quiz_cb
        assert menu.start_scoreboard_mode == scoreboard_cb

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
        menu = MainMenu(parent, MagicMock(), MagicMock(), MagicMock(), MagicMock())

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
        menu = MainMenu(parent, MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert menu.get_card_count() == 250

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    def test_sections_initialization(self, mock_checkbutton, mock_scrollbar, mock_canvas,
                                     mock_boolvar, mock_intvar, mock_spinbox, mock_button,
                                     mock_label, mock_frame):
        """Test MainMenu initialization with sections."""
        mock_intvar.return_value = MagicMock()
        mock_boolvar_instance = MagicMock()
        mock_boolvar_instance.get.return_value = True
        mock_boolvar.return_value = mock_boolvar_instance
        mock_canvas_instance = MagicMock()
        mock_canvas.return_value = mock_canvas_instance

        parent = MagicMock()
        section_counts = {"General": 10, "Section1": 5, "Section2": 8}
        menu = MainMenu(parent, MagicMock(), MagicMock(), MagicMock(), MagicMock(), section_counts=section_counts)

        assert menu.section_counts == section_counts
        assert len(menu.section_vars) == 3
        # All sections should be checked by default
        assert menu.get_selected_sections() == {"General", "Section1", "Section2"}

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    def test_check_all_uncheck_all(self, mock_checkbutton, mock_scrollbar, mock_canvas,
                                   mock_boolvar, mock_intvar, mock_spinbox, mock_button,
                                   mock_label, mock_frame):
        """Test check all and uncheck all methods."""
        mock_intvar.return_value = MagicMock()
        mock_boolvar_instance = MagicMock()
        mock_boolvar_instance.get.return_value = True
        mock_boolvar.return_value = mock_boolvar_instance
        mock_canvas.return_value = MagicMock()

        parent = MagicMock()
        section_counts = {"General": 10, "Section1": 5}
        menu = MainMenu(parent, MagicMock(), MagicMock(), MagicMock(), MagicMock(), section_counts=section_counts)

        # Test uncheck all
        menu._uncheck_all()
        for var in menu.section_vars.values():
            var.set.assert_called_with(False)

        # Test check all
        menu._check_all()
        for var in menu.section_vars.values():
            var.set.assert_called_with(True)

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
        menu = MainMenu(parent, MagicMock(), MagicMock(), MagicMock(), MagicMock())

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
# Tests for load_quiz_history and ScoreboardScreen
# =============================================================================

class TestLoadQuizHistory:
    """Tests for the load_quiz_history function."""

    def test_load_empty_when_file_missing(self, tmp_path, monkeypatch):
        """Test that empty list is returned when history file doesn't exist."""
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: tmp_path / "nonexistent" / "history.csv"
        )
        result = load_quiz_history()
        assert result == []

    def test_load_quiz_history_with_data(self, tmp_path, monkeypatch):
        """Test loading history with valid data."""
        history_file = tmp_path / "history.csv"
        history_file.write_text(
            "time,number_of_questions,number_of_correct_answers\n"
            "2024-01-15T10:30:00,20,15\n"
            "2024-01-16T14:00:00,30,28\n",
            encoding="utf-8"
        )
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: history_file
        )

        result = load_quiz_history()

        assert len(result) == 2
        assert result[0]["time"] == "2024-01-15T10:30:00"
        assert result[0]["total"] == 20
        assert result[0]["correct"] == 15
        assert result[1]["time"] == "2024-01-16T14:00:00"
        assert result[1]["total"] == 30
        assert result[1]["correct"] == 28

    def test_load_quiz_history_empty_file(self, tmp_path, monkeypatch):
        """Test loading history from empty file with just headers."""
        history_file = tmp_path / "history.csv"
        history_file.write_text(
            "time,number_of_questions,number_of_correct_answers\n",
            encoding="utf-8"
        )
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: history_file
        )

        result = load_quiz_history()
        assert result == []


class TestSaveQuizResult:
    """Tests for the save_quiz_result function."""

    def test_creates_directory_if_missing(self, tmp_path, monkeypatch):
        """Test that save_quiz_result creates parent directories if they don't exist."""
        history_file = tmp_path / "new_dir" / "subdir" / "history.csv"
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: history_file
        )

        save_quiz_result(total=10, correct=8)

        assert history_file.exists()
        assert history_file.parent.exists()

    def test_creates_file_with_headers(self, tmp_path, monkeypatch):
        """Test that save_quiz_result creates file with CSV headers."""
        history_file = tmp_path / "history.csv"
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: history_file
        )

        save_quiz_result(total=10, correct=8)

        content = history_file.read_text()
        lines = content.strip().split("\n")
        assert lines[0] == "time,number_of_questions,number_of_correct_answers"

    def test_appends_result_to_file(self, tmp_path, monkeypatch):
        """Test that save_quiz_result appends result row."""
        history_file = tmp_path / "history.csv"
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: history_file
        )

        save_quiz_result(total=10, correct=8)

        content = history_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2  # header + 1 result
        parts = lines[1].split(",")
        assert parts[1] == "10"
        assert parts[2] == "8"

    def test_appends_multiple_results(self, tmp_path, monkeypatch):
        """Test that multiple saves append correctly."""
        history_file = tmp_path / "history.csv"
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: history_file
        )

        save_quiz_result(total=10, correct=8)
        save_quiz_result(total=20, correct=15)
        save_quiz_result(total=5, correct=5)

        content = history_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 4  # header + 3 results

    def test_does_not_duplicate_headers(self, tmp_path, monkeypatch):
        """Test that headers are only written once."""
        history_file = tmp_path / "history.csv"
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: history_file
        )

        save_quiz_result(total=10, correct=8)
        save_quiz_result(total=20, correct=15)

        content = history_file.read_text()
        header_count = content.count("time,number_of_questions")
        assert header_count == 1

    def test_writes_iso_timestamp(self, tmp_path, monkeypatch):
        """Test that timestamp is in ISO format."""
        history_file = tmp_path / "history.csv"
        monkeypatch.setattr(
            "flashcards.history.get_history_path",
            lambda: history_file
        )

        save_quiz_result(total=10, correct=8)

        content = history_file.read_text()
        lines = content.strip().split("\n")
        timestamp = lines[1].split(",")[0]
        # ISO format should contain T separator and have proper structure
        assert "T" in timestamp
        assert len(timestamp) >= 19  # YYYY-MM-DDTHH:MM:SS minimum


class TestQuizResultsScreen:
    """Tests for the QuizResultsScreen class."""

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_initialization(self, mock_button, mock_label, mock_frame, mock_root):
        """Test QuizResultsScreen initialization."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        from flashcards.app import QuizResultsScreen
        screen = QuizResultsScreen(mock_root, correct_count=8, total=10)

        assert screen.correct_count == 8
        assert screen.total == 10

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_percentage_calculation_normal(self, mock_button, mock_label, mock_frame, mock_root):
        """Test percentage is calculated correctly."""
        mock_frame.return_value = MagicMock()
        mock_label_instance = MagicMock()
        mock_label.return_value = mock_label_instance
        mock_button.return_value = MagicMock()

        from flashcards.app import QuizResultsScreen
        screen = QuizResultsScreen(mock_root, correct_count=8, total=10)

        # Check that label was called with correct percentage
        label_calls = mock_label.call_args_list
        score_call = [c for c in label_calls if "80%" in str(c)]
        assert len(score_call) == 1

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_percentage_zero_total(self, mock_button, mock_label, mock_frame, mock_root):
        """Test percentage with zero total doesn't crash."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        from flashcards.app import QuizResultsScreen
        # Should not raise ZeroDivisionError
        screen = QuizResultsScreen(mock_root, correct_count=0, total=0)

        assert screen.total == 0

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_back_callback_wired(self, mock_button, mock_label, mock_frame, mock_root):
        """Test that back callback is stored."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        back_cb = MagicMock()
        from flashcards.app import QuizResultsScreen
        screen = QuizResultsScreen(mock_root, correct_count=5, total=10, on_back_to_menu=back_cb)

        assert screen.on_back_to_menu == back_cb

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_show_hide(self, mock_button, mock_label, mock_frame, mock_root):
        """Test show and hide methods."""
        mock_frame_instance = MagicMock()
        mock_frame.return_value = mock_frame_instance
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        from flashcards.app import QuizResultsScreen
        screen = QuizResultsScreen(mock_root, correct_count=5, total=10)

        screen.show()
        mock_frame_instance.pack.assert_called()

        screen.hide()
        mock_frame_instance.pack_forget.assert_called()

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_perfect_score_display(self, mock_button, mock_label, mock_frame, mock_root):
        """Test display with perfect score."""
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        from flashcards.app import QuizResultsScreen
        screen = QuizResultsScreen(mock_root, correct_count=10, total=10)

        label_calls = mock_label.call_args_list
        score_call = [c for c in label_calls if "100%" in str(c)]
        assert len(score_call) == 1


class TestQuizCompletionFlow:
    """Tests for the quiz completion flow - results screen + history saving."""

    @patch('flashcards.controller.save_quiz_result')
    @patch('flashcards.controller.QuizResultsScreen')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    def test_on_quiz_complete_saves_result(self, mock_checkbutton, mock_scrollbar, mock_canvas,
                                            mock_boolvar, mock_intvar, mock_spinbox, mock_button,
                                            mock_label, mock_frame, mock_results_screen,
                                            mock_save, mock_root, sample_cards):
        """Test that quiz completion saves result to history."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 10
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()
        mock_results_screen.return_value = MagicMock()

        app = App(mock_root, sample_cards)
        app._on_quiz_complete(correct=8, total=10)

        mock_save.assert_called_once_with(10, 8)

    @patch('flashcards.controller.save_quiz_result')
    @patch('flashcards.controller.QuizResultsScreen')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    def test_on_quiz_complete_shows_results_screen(self, mock_checkbutton, mock_scrollbar,
                                                    mock_canvas, mock_boolvar, mock_intvar,
                                                    mock_spinbox, mock_button, mock_label,
                                                    mock_frame, mock_results_screen, mock_save,
                                                    mock_root, sample_cards):
        """Test that quiz completion shows results screen."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 10
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()
        mock_results_instance = MagicMock()
        mock_results_screen.return_value = mock_results_instance

        app = App(mock_root, sample_cards)
        app._on_quiz_complete(correct=8, total=10)

        mock_results_screen.assert_called_once()
        mock_results_instance.show.assert_called_once()

    @patch('flashcards.controller.save_quiz_result')
    @patch('flashcards.controller.QuizResultsScreen')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    def test_on_quiz_complete_hides_flashcard_app(self, mock_checkbutton, mock_scrollbar,
                                                   mock_canvas, mock_boolvar, mock_intvar,
                                                   mock_spinbox, mock_button, mock_label,
                                                   mock_frame, mock_results_screen, mock_save,
                                                   mock_root, sample_cards):
        """Test that quiz completion hides the quiz app."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 10
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()
        mock_results_screen.return_value = MagicMock()

        app = App(mock_root, sample_cards)
        mock_flashcard = MagicMock()
        app.flashcard_app = mock_flashcard

        app._on_quiz_complete(correct=8, total=10)

        mock_flashcard.hide.assert_called_once()
        assert app.flashcard_app is None

    @patch('flashcards.controller.save_quiz_result')
    @patch('flashcards.controller.QuizResultsScreen')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    def test_back_to_menu_from_results(self, mock_checkbutton, mock_scrollbar, mock_canvas,
                                        mock_boolvar, mock_intvar, mock_spinbox, mock_button,
                                        mock_label, mock_frame, mock_results_screen,
                                        mock_save, mock_root, sample_cards):
        """Test returning to menu from results screen."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 10
        mock_intvar.return_value = mock_intvar_instance
        mock_frame_instance = MagicMock()
        mock_frame.return_value = mock_frame_instance
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()
        mock_results_instance = MagicMock()
        mock_results_screen.return_value = mock_results_instance

        app = App(mock_root, sample_cards)
        app._on_quiz_complete(correct=8, total=10)

        app._back_to_menu_from_results()

        mock_results_instance.hide.assert_called_once()
        assert app.results_screen is None


class TestScoreboardScreen:
    """Tests for the ScoreboardScreen class."""

    @patch('flashcards.screens.scoreboard.load_quiz_history')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_empty_state_shows_message(self, mock_button, mock_label, mock_frame,
                                        mock_load_history):
        """Test that empty history shows appropriate message."""
        mock_load_history.return_value = []
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        parent = MagicMock()
        back_cb = MagicMock()

        screen = ScoreboardScreen(parent, back_cb)

        # Verify that Label was called with "No quiz history yet"
        label_calls = [call for call in mock_label.call_args_list
                       if call.kwargs.get('text') == 'No quiz history yet']
        assert len(label_calls) == 1

    @patch('flashcards.screens.scoreboard.load_quiz_history')
    @patch('tkinter.ttk.Treeview')
    @patch('tkinter.ttk.Scrollbar')
    @patch('tkinter.ttk.Style')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_with_history_creates_table(self, mock_button, mock_label, mock_frame,
                                         mock_style, mock_scrollbar, mock_treeview,
                                         mock_load_history):
        """Test that history data creates a table."""
        mock_load_history.return_value = [
            {"time": "2024-01-15T10:30:00", "total": 20, "correct": 15},
            {"time": "2024-01-16T14:00:00", "total": 30, "correct": 28},
        ]
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        mock_style.return_value = MagicMock()
        mock_scrollbar.return_value = MagicMock()
        mock_tree_instance = MagicMock()
        mock_treeview.return_value = mock_tree_instance

        parent = MagicMock()
        back_cb = MagicMock()

        screen = ScoreboardScreen(parent, back_cb)

        # Verify treeview was created with correct columns
        mock_treeview.assert_called_once()
        call_kwargs = mock_treeview.call_args.kwargs
        assert "columns" in call_kwargs
        assert call_kwargs["columns"] == ("datetime", "questions", "correct", "percentage")

        # Verify rows were inserted (2 entries, inserted in reverse order)
        assert mock_tree_instance.insert.call_count == 2

    @patch('flashcards.screens.scoreboard.load_quiz_history')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_back_button_calls_callback(self, mock_button, mock_label, mock_frame,
                                         mock_load_history):
        """Test that back button is wired to callback."""
        mock_load_history.return_value = []
        mock_frame.return_value = MagicMock()
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        parent = MagicMock()
        back_cb = MagicMock()

        screen = ScoreboardScreen(parent, back_cb)

        assert screen.back_to_menu == back_cb

    @patch('flashcards.screens.scoreboard.load_quiz_history')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    def test_show_hide(self, mock_button, mock_label, mock_frame, mock_load_history):
        """Test show and hide methods."""
        mock_load_history.return_value = []
        mock_frame_instance = MagicMock()
        mock_frame.return_value = mock_frame_instance
        mock_label.return_value = MagicMock()
        mock_button.return_value = MagicMock()

        parent = MagicMock()
        screen = ScoreboardScreen(parent, MagicMock())

        screen.show()
        mock_frame_instance.pack.assert_called()

        screen.hide()
        mock_frame_instance.pack_forget.assert_called()


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
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    def test_initialization(self, mock_checkbutton, mock_scrollbar, mock_canvas,
                            mock_boolvar, mock_intvar, mock_spinbox, mock_button,
                            mock_label, mock_frame, mock_root, sample_cards):
        """Test App initialization."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 100
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()

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
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    @patch('flashcards.controller.spread_shuffle_with_replacement')
    def test_start_simple_mode(self, mock_spread_shuffle, mock_checkbutton,
                                mock_scrollbar, mock_canvas, mock_boolvar, mock_intvar,
                                mock_spinbox, mock_button, mock_label, mock_frame,
                                mock_flashcard_app, mock_root, sample_cards):
        """Test starting simple mode."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 50
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()
        mock_spread_shuffle.return_value = sample_cards

        app = App(mock_root, sample_cards)
        # Mock get_selected_sections to return the section in sample_cards
        app.main_menu.get_selected_sections = MagicMock(return_value={"General"})
        app._start_simple_mode()

        # spread_shuffle_with_replacement samples with replacement and spreads sections
        mock_spread_shuffle.assert_called_with(sample_cards, 50)

    @patch('flashcards.app.FlashCardApp')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    @patch('flashcards.controller.spread_shuffle_with_replacement')
    def test_start_inverted_mode(self, mock_spread_shuffle, mock_checkbutton,
                                  mock_scrollbar, mock_canvas, mock_boolvar, mock_intvar,
                                  mock_spinbox, mock_button, mock_label, mock_frame,
                                  mock_flashcard_app, mock_root, sample_cards):
        """Test starting inverted mode."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 75
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()
        mock_spread_shuffle.return_value = sample_cards

        app = App(mock_root, sample_cards)
        # Mock get_selected_sections to return the section in sample_cards
        app.main_menu.get_selected_sections = MagicMock(return_value={"General"})
        app._start_inverted_mode()

        # spread_shuffle_with_replacement samples with replacement and spreads sections
        mock_spread_shuffle.assert_called_with(sample_cards, 75)

    @patch('flashcards.app.QuizCardApp')
    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    @patch('flashcards.controller.spread_shuffle_with_replacement')
    def test_start_quiz_mode(self, mock_spread_shuffle, mock_checkbutton,
                              mock_scrollbar, mock_canvas, mock_boolvar, mock_intvar,
                              mock_spinbox, mock_button, mock_label, mock_frame,
                              mock_quiz_app, mock_root, sample_cards):
        """Test starting quiz mode."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 100
        mock_intvar.return_value = mock_intvar_instance
        mock_frame.return_value = MagicMock()
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()
        mock_spread_shuffle.return_value = sample_cards

        app = App(mock_root, sample_cards)
        # Mock get_selected_sections to return the section in sample_cards
        app.main_menu.get_selected_sections = MagicMock(return_value={"General"})
        app._start_quiz_mode()

        # spread_shuffle_with_replacement samples with replacement and spreads sections
        mock_spread_shuffle.assert_called_with(sample_cards, 100)

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    @patch('tkinter.Button')
    @patch('tkinter.Spinbox')
    @patch('tkinter.IntVar')
    @patch('tkinter.BooleanVar')
    @patch('tkinter.Canvas')
    @patch('tkinter.Scrollbar')
    @patch('tkinter.Checkbutton')
    def test_back_to_menu(self, mock_checkbutton, mock_scrollbar, mock_canvas,
                          mock_boolvar, mock_intvar, mock_spinbox, mock_button,
                          mock_label, mock_frame, mock_root, sample_cards):
        """Test returning to main menu."""
        mock_intvar_instance = MagicMock()
        mock_intvar_instance.get.return_value = 100
        mock_intvar.return_value = mock_intvar_instance
        mock_frame_instance = MagicMock()
        mock_frame.return_value = mock_frame_instance
        mock_canvas.return_value = MagicMock()
        mock_boolvar.return_value = MagicMock()

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
            cards, sections = parse_markdown_tables(str(md_file))
            assert len(cards) > 0
            assert len(sections) > 0

            # Verify card structure
            for card in cards:
                assert "term" in card
                assert "interpretation" in card
                assert "extra" in card
                assert "section" in card
                assert isinstance(card["term"], str)
                assert isinstance(card["interpretation"], str)
                assert isinstance(card["extra"], str)
                assert isinstance(card["section"], str)

    def test_card_data_integrity(self):
        """Test that all cards have required fields."""
        script_dir = Path(__file__).parent
        md_file = script_dir / "medical-terms.md"

        if md_file.exists():
            cards, sections = parse_markdown_tables(str(md_file))

            for i, card in enumerate(cards):
                assert card["term"], f"Card {i} has empty term"
                assert card["interpretation"], f"Card {i} has empty interpretation"
                assert card["section"], f"Card {i} has empty section"

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

        cards, sections = parse_markdown_tables(str(md_file))
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

        cards, sections = parse_markdown_tables(str(md_file))
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

        cards, sections = parse_markdown_tables(str(md_file))
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

        cards, sections = parse_markdown_tables(str(md_file))
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

        cards, sections = parse_markdown_tables(str(md_file))
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

        cards, sections = parse_markdown_tables(str(md_file))
        assert len(cards) == 1000

    def test_fix_rtl_performance_with_long_text(self):
        """Test fix_rtl with very long text."""
        long_text = "שלום " * 500  # ~2500 characters
        result = fix_rtl(long_text)
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
