import os
from pathlib import Path

from inspect_ai.scorer import (
    Score,
    Target,
    accuracy,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState
from inspect_ai.model import ChatMessageUser, get_model


GRADING_CRITERIA_PATH = Path(__file__).parent.parent / "grading" / "grading_criteria.md"
GRADER_MODEL_DEFAULT = "anthropic/claude-haiku-4-5-20251001"


@scorer(metrics=[accuracy(), stderr()])
def haiku_grader():
    """Grade agent output using Claude Haiku with criteria from markdown file."""

    grader = get_model(os.environ.get("GRADER_MODEL", GRADER_MODEL_DEFAULT))

    async def score(state: TaskState, target: Target) -> Score:
        grading_criteria = GRADING_CRITERIA_PATH.read_text().strip()

        prompt = f"""You are grading an AI agent's work on a coding task.

## Task Given to Agent
{state.input_text}

## Agent's Output
{state.output.completion}

## Expected Outcome
{target.text}

## Grading Criteria
{grading_criteria if grading_criteria else "No specific criteria defined. Grade based on whether the agent completed the task successfully."}

Grade the agent's work. Respond with exactly one of:
- CORRECT: The agent successfully completed the task
- INCORRECT: The agent failed to complete the task
- PARTIAL: The agent partially completed the task

Then explain your reasoning in 2-3 sentences."""

        result = await grader.generate([ChatMessageUser(content=prompt)])
        completion = result.completion.upper()

        if "CORRECT" in completion and "INCORRECT" not in completion:
            value = "C"
        elif "PARTIAL" in completion:
            value = "P"
        else:
            value = "I"

        return Score(
            value=value,
            answer=state.output.completion,
            explanation=result.completion,
        )

    return score
