import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scorer.haiku_grader import haiku_grader


@pytest.fixture
def criteria_file(tmp_path):
    f = tmp_path / "grading_criteria.md"
    f.write_text("Award full marks if all tests pass.")
    return f


@pytest.fixture
def mock_state():
    state = MagicMock()
    state.input_text = "Fix the failing tests"
    state.output.completion = "I ran cargo test and all tests pass now."
    return state


@pytest.fixture
def mock_target():
    target = MagicMock()
    target.text = "All tests pass."
    return target


def _grader_result(text):
    r = MagicMock()
    r.completion = text
    return r


async def test_score_value_is_C_for_correct(criteria_file, mock_state, mock_target):
    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file):
        mock_model = MagicMock()
        mock_model.generate = AsyncMock(return_value=_grader_result("CORRECT: Agent passed all tests."))
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        result = await score_fn(mock_state, mock_target)

    assert result.value == "C"


async def test_score_value_is_P_for_partial(criteria_file, mock_state, mock_target):
    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file):
        mock_model = MagicMock()
        mock_model.generate = AsyncMock(return_value=_grader_result("PARTIAL: Agent fixed some tests."))
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        result = await score_fn(mock_state, mock_target)

    assert result.value == "P"


async def test_score_value_is_I_for_incorrect(criteria_file, mock_state, mock_target):
    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file):
        mock_model = MagicMock()
        mock_model.generate = AsyncMock(return_value=_grader_result("INCORRECT: Agent did nothing."))
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        result = await score_fn(mock_state, mock_target)

    assert result.value == "I"


async def test_criteria_read_at_score_time_not_construction(tmp_path, mock_state, mock_target):
    criteria_file = tmp_path / "grading_criteria.md"
    criteria_file.write_text("initial criteria")

    captured = []

    async def fake_generate(messages):
        captured.append(messages[0].content)
        return _grader_result("CORRECT: done.")

    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file):
        mock_model = MagicMock()
        mock_model.generate = fake_generate
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        criteria_file.write_text("updated criteria")
        await score_fn(mock_state, mock_target)

    assert "updated criteria" in captured[0]
    assert "initial criteria" not in captured[0]


async def test_grader_model_from_env(criteria_file, mock_state, mock_target):
    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch.dict(os.environ, {"GRADER_MODEL": "anthropic/claude-opus-4-7"}):
        mock_model = MagicMock()
        mock_model.generate = AsyncMock(return_value=_grader_result("CORRECT: done."))
        mock_get_model.return_value = mock_model

        haiku_grader()

    mock_get_model.assert_called_once_with("anthropic/claude-opus-4-7")
