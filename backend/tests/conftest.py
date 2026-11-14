import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hub.db import connect  # noqa: E402


@pytest.fixture
def conn():
    c = connect(":memory:")
    yield c
    c.close()


@pytest.fixture(scope="session")
def imported(tmp_path_factory):
    """One full import of the real local data into a temp DB (shared, read-mostly)."""
    from hub.ingestion import pipeline
    c = connect(tmp_path_factory.mktemp("db") / "hub.sqlite")
    result = pipeline.run_all(c)
    return c, result
