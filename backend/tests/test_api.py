import importlib.util
from pathlib import Path

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


def test_vercel_entrypoint_imports_asgi_app():
    entrypoint = Path(__file__).resolve().parents[2] / "api" / "index.py"
    spec = importlib.util.spec_from_file_location("vercel_entrypoint", entrypoint)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.app.title == "Windwatch UK"
