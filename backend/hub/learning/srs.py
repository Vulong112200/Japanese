"""SM-2 style scheduler with Again/Hard/Good/Easy (spec Part 8). Pure functions, no DB."""
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta

RATINGS = ("again", "hard", "good", "easy")
MIN_EASE = 1.3
MASTERED_INTERVAL = 21      # days
MASTERED_REPS = 3           # consecutive successful reviews — never mastered after one answer
ATTENTION_LAPSES = 3
LEARNING_STEP_MIN = 10      # minutes until an "again" card comes back
# SRS cấp tốc (ADR-030): compressed ladder for the weeks before the exam
INTENSIVE_STEPS = (LEARNING_STEP_MIN / 1440, 1, 2, 4, 7)   # days; reps 0,1,2,3,≥4 -> next interval
INTENSIVE_MAX = INTENSIVE_STEPS[-1]
INTENSIVE_MASTERED_REPS = 5  # 5 correct in a row, the last one after a 4-day gap


@dataclass(frozen=True)
class Card:
    ease: float = 2.5
    interval_days: float = 0
    reps: int = 0
    lapses: int = 0
    review_count: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    status: str = "new"


def classify(c: Card) -> str:
    """Mode-independent, so mixing normal and cấp tốc reviews never hides a mastered card."""
    if c.review_count == 0:
        return "new"
    if c.lapses >= ATTENTION_LAPSES and c.reps < MASTERED_REPS:
        return "needs_attention"
    if c.reps == 0:
        return "learning"
    if c.reps >= INTENSIVE_MASTERED_REPS or (c.interval_days >= MASTERED_INTERVAL and c.reps >= MASTERED_REPS):
        return "mastered"
    return "reviewing"


def _intensive_interval(c: Card, rating: str, now: datetime, exam_date: date | None) -> float:
    last = len(INTENSIVE_STEPS) - 1
    idx = min(last, c.reps + {"hard": -1, "good": 0, "easy": 1}[rating])
    interval = INTENSIVE_STEPS[max(0, idx)]
    if exam_date:
        days_left = (exam_date - now.date()).days - 1   # always one more look before exam day
        if days_left >= 1:
            interval = min(interval, days_left)
    return interval


def intensive_gap(reps: int) -> float:
    """Days after the last review at which a card with this streak is due in SRS cấp tốc — also for cards that
    normal SM-2 booked further out (read-time, repo.due_cards)."""
    return INTENSIVE_STEPS[min(max(reps, 1), len(INTENSIVE_STEPS)) - 1]


def schedule(c: Card, rating: str, now: datetime, intensive: bool = False,
             exam_date: date | None = None) -> tuple[Card, datetime]:
    if rating not in RATINGS:
        raise ValueError(f"rating must be one of {RATINGS}")
    c = replace(c, review_count=c.review_count + 1)
    if rating == "again":
        c = replace(c, reps=0, lapses=c.lapses + (1 if c.review_count > 1 else 0),
                    ease=max(MIN_EASE, c.ease - 0.2), interval_days=0,
                    incorrect_count=c.incorrect_count + 1)
        c = replace(c, status=classify(c))
        return c, now + timedelta(minutes=LEARNING_STEP_MIN)

    ease = c.ease + {"hard": -0.15, "good": 0.0, "easy": 0.15}[rating]
    ease = max(MIN_EASE, ease)
    if intensive:
        interval = _intensive_interval(c, rating, now, exam_date)
    elif c.reps == 0:
        interval = {"hard": 1, "good": 1, "easy": 4}[rating]
    elif c.reps == 1:
        interval = {"hard": 3, "good": 6, "easy": 8}[rating]
    else:
        mult = {"hard": 1.2, "good": ease, "easy": ease * 1.3}[rating]
        interval = max(c.interval_days + 1, round(c.interval_days * mult))
    c = replace(c, ease=ease, interval_days=interval, reps=c.reps + 1, correct_count=c.correct_count + 1)
    c = replace(c, status=classify(c))
    return c, now + timedelta(days=interval)
