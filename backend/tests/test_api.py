import pytest
from fastapi import HTTPException
from app.main import days, health, _valid


def test_health():
    assert health()["status"] == "ok"


def test_days():
    assert len(days()["days"]) == 31


def test_date_guard():
    with pytest.raises(HTTPException) as error:
        _valid("2025-12-31")
    assert error.value.status_code == 422
