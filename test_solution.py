"""Unit tests for automated solution."""
import pytest
from solution import solve_task

def test_solve_task_success():
    res = solve_task({"key": "value"})
    assert res["status"] == "success"
    assert res["processed"] is True

def test_solve_task_invalid():
    with pytest.raises(ValueError):
        solve_task("invalid")
