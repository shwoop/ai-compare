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


def _mock_sandbox(diff="+ fn mute_with_duration() {}", test_output="test result: ok. 3 passed"):
    mock_sb = MagicMock()
    mock_sb.exec = AsyncMock(side_effect=[
        MagicMock(success=True, returncode=0, stdout=diff, stderr=""),
        MagicMock(success=True, returncode=0, stdout=test_output, stderr=""),
    ])
    return mock_sb


async def test_score_value_is_C_for_correct(criteria_file, mock_state, mock_target):
    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", return_value=_mock_sandbox()):
        mock_model = MagicMock()
        mock_model.generate = AsyncMock(return_value=_grader_result("CORRECT: Agent passed all tests."))
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        result = await score_fn(mock_state, mock_target)

    assert result.value == "C"


async def test_score_value_is_P_for_partial(criteria_file, mock_state, mock_target):
    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", return_value=_mock_sandbox()):
        mock_model = MagicMock()
        mock_model.generate = AsyncMock(return_value=_grader_result("PARTIAL: Agent fixed some tests."))
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        result = await score_fn(mock_state, mock_target)

    assert result.value == "P"


async def test_score_value_is_I_for_incorrect(criteria_file, mock_state, mock_target):
    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", return_value=_mock_sandbox()):
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
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", return_value=_mock_sandbox()):
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
         patch("scorer.haiku_grader.sandbox", return_value=_mock_sandbox()), \
         patch.dict(os.environ, {"GRADER_MODEL": "anthropic/claude-opus-4-7"}):
        mock_model = MagicMock()
        mock_model.generate = AsyncMock(return_value=_grader_result("CORRECT: done."))
        mock_get_model.return_value = mock_model

        haiku_grader()

    mock_get_model.assert_called_once_with("anthropic/claude-opus-4-7")


async def test_git_diff_included_in_prompt(criteria_file, mock_state, mock_target):
    captured = []

    async def fake_generate(messages):
        captured.append(messages[0].content)
        return _grader_result("CORRECT: done.")

    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", return_value=_mock_sandbox(diff="+ fn mute_with_duration() {}")):
        mock_model = MagicMock()
        mock_model.generate = fake_generate
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        await score_fn(mock_state, mock_target)

    assert "Actual Code Changes" in captured[0]
    assert "+ fn mute_with_duration() {}" in captured[0]


async def test_cargo_test_included_in_prompt(criteria_file, mock_state, mock_target):
    captured = []

    async def fake_generate(messages):
        captured.append(messages[0].content)
        return _grader_result("CORRECT: done.")

    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", return_value=_mock_sandbox(test_output="test result: ok. 5 passed")):
        mock_model = MagicMock()
        mock_model.generate = fake_generate
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        await score_fn(mock_state, mock_target)

    assert "Test Results" in captured[0]
    assert "test result: ok. 5 passed" in captured[0]


async def test_git_diff_truncated_when_large(criteria_file, mock_state, mock_target):
    large_diff = "+" + "x" * 9000

    captured = []

    async def fake_generate(messages):
        captured.append(messages[0].content)
        return _grader_result("CORRECT: done.")

    mock_sb = MagicMock()
    mock_sb.exec = AsyncMock(side_effect=[
        MagicMock(success=True, returncode=0, stdout=large_diff, stderr=""),
        MagicMock(success=True, returncode=0, stdout="test result: ok", stderr=""),
    ])

    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", return_value=mock_sb):
        mock_model = MagicMock()
        mock_model.generate = fake_generate
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        await score_fn(mock_state, mock_target)

    assert "truncated" in captured[0]


async def test_git_diff_fallback_when_sandbox_unavailable(criteria_file, mock_state, mock_target):
    captured = []

    async def fake_generate(messages):
        captured.append(messages[0].content)
        return _grader_result("CORRECT: done.")

    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", side_effect=RuntimeError("no sandbox")):
        mock_model = MagicMock()
        mock_model.generate = fake_generate
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        await score_fn(mock_state, mock_target)

    assert "git diff unavailable" in captured[0]


async def test_cargo_test_timeout_handled(criteria_file, mock_state, mock_target):
    captured = []

    async def fake_generate(messages):
        captured.append(messages[0].content)
        return _grader_result("CORRECT: done.")

    mock_sb = MagicMock()
    mock_sb.exec = AsyncMock(side_effect=[
        MagicMock(success=True, returncode=0, stdout="+ some diff", stderr=""),
        TimeoutError("timed out"),
    ])

    with patch("scorer.haiku_grader.get_model") as mock_get_model, \
         patch("scorer.haiku_grader.GRADING_CRITERIA_PATH", criteria_file), \
         patch("scorer.haiku_grader.sandbox", return_value=mock_sb):
        mock_model = MagicMock()
        mock_model.generate = fake_generate
        mock_get_model.return_value = mock_model

        score_fn = haiku_grader()
        await score_fn(mock_state, mock_target)

    assert "TIMED OUT" in captured[0]
