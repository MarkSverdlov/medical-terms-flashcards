"""Quiz history persistence module."""

import csv
from datetime import datetime
from pathlib import Path


def get_history_path() -> Path:
    """Return the path to the history CSV file."""
    return Path.home() / ".local" / "share" / "flashcards" / "history.csv"


def save_quiz_result(total: int, correct: int) -> None:
    """Append a quiz result to the history CSV file.

    Creates the directory and file if they don't exist.

    Args:
        total: Total number of questions in the quiz.
        correct: Number of correct answers.
    """
    history_path = get_history_path()
    history_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = history_path.exists()

    with open(history_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["time", "number_of_questions", "number_of_correct_answers"])
        writer.writerow([datetime.now().isoformat(), total, correct])


def load_quiz_history() -> list[dict]:
    """Load quiz history from the CSV file.

    Returns:
        List of dictionaries with keys: time, total, correct.
        Returns empty list if file doesn't exist.
    """
    history_path = get_history_path()
    if not history_path.exists():
        return []

    results = []
    with open(history_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "time": row["time"],
                "total": int(row["number_of_questions"]),
                "correct": int(row["number_of_correct_answers"]),
            })
    return results
