# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the application
flashcards
# or: python -m flashcards

# Run tests
pytest flashcards/test_app.py -v

# Run a single test
pytest flashcards/test_app.py::TestClassName::test_method -v
```

## Architecture

Medical Flashcards is a Tkinter-based educational app for learning medical terminology with Hebrew translations.

### Controller Pattern
- **App** (`controller.py`): Main coordinator managing screen navigation and state
- Screens use `show()`/`hide()` methods for transitions

### Screens (`screens/`)
- **MainMenu**: Card count selection, section filtering, mode selection
- **FlashCardApp**: Simple (term→interpretation) and Inverted modes with click-to-flip
- **QuizCardApp**: Type-to-answer mode with partial credit scoring
- **QuizResultsScreen**: Score summary after quiz completion
- **ScoreboardScreen**: Historical quiz results table

### Data Flow
1. `medical-terms.md` → `parse_markdown_tables()` → card list
2. Cards filtered by selected sections in MainMenu
3. Cards shuffled and limited to requested count
4. Screen displays cards with navigation

### Card Structure
```python
{"term": str, "interpretation": str, "extra": str, "section": str}
```

### Key Utilities (`utils.py`)
- `fix_rtl()`: Hebrew text display using python-bidi
- `parse_markdown_tables()`: Extracts cards from markdown
- `calculate_font_size()`: Dynamic sizing based on text length

### Persistence (`history.py`)
Quiz history stored as CSV at `~/.local/share/flashcards/history.csv`

## Medical Terms Data

Terms live in `flashcards/medical-terms.md` as markdown tables with sections marked by `=====` underlines. Format: Term | Interpretation | Example

## Answer Validation

Quiz answers are normalized: case-insensitive, dash-insensitive, supports comma-separated alternatives. Credit given for subset matches.
