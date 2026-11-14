"""SM-2 style scheduler with Again/Hard/Good/Easy (spec Part 8). Pure functions, no DB."""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

RATINGS = ("again", "hard", "good", "easy")
MIN_EASE = 1.3
MASTERED_INTERVAL = 21      # days
MASTERED_REPS = 3           # consecutive successful reviews — never mastered after one answer
ATTENTION_LAPSES = 3
LEARNING_STEP_MIN = 10      # minutes until an "again" card comes back


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
    if c.review_count == 0:
        return "new"
    if c.lapses >= ATTENTION_LAPSES and c.reps < MASTERED_REPS:
        return "needs_attention"
    if c.reps == 0:
        return "learning"
    if c.interval_days >= MASTERED_INTERVAL and c.reps >= MASTERED_REPS:
        return "mastered"
    return "reviewing"


def schedule(c: Card, rating: str, now: datetime) -> tuple[Card, datetime]:
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
    if c.reps == 0:
        interval = {"hard": 1, "good": 1, "easy": 4}[rating]
    elif c.reps == 1:
        interval = {"hard": 3, "good": 6, "easy": 8}[rating]
    else:
        mult = {"hard": 1.2, "good": ease, "easy": ease * 1.3}[rating]
        interval = max(c.interval_days + 1, round(c.interval_days * mult))
    c = replace(c, ease=ease, interval_days=interval, reps=c.reps + 1, correct_count=c.correct_count + 1)
    c = replace(c, status=classify(c))
    return c, now + timedelta(days=interval)
