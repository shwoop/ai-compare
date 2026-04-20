import os
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_swe import claude_code

from scorer.haiku_grader import haiku_grader


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "task_prompt.md"
REPO_URL_DEFAULT = "https://github.com/shwoop/siggy.git"


def make_dataset() -> MemoryDataset:
    """Create the evaluation dataset with a single sample."""

    repo_url = os.environ.get("REPO_URL", REPO_URL_DEFAULT)
    task_prompt = PROMPT_PATH.read_text().strip()

    return MemoryDataset([
        Sample(
            id="clone-and-solve",
            input=task_prompt,
            target="The timed mute feature is implemented: /mute accepts an optional duration (1h, 8h, 1d, 1w), the expiry is stored in the database, and notifications respect the expiry. All tests pass.",
            setup=f"""#!/bin/bash
set -euo pipefail
git clone --single-branch --branch 190-base {repo_url} /workspace
echo "Repo cloned successfully"
""",
            metadata={
                "repo_url": repo_url,
            },
        )
    ])


@task
def clone_and_solve() -> Task:
    """Clone a Rust repo, read the task prompt, solve it with Claude Code."""
    return Task(
        dataset=make_dataset(),
        solver=claude_code(
            system_prompt="You are working in /workspace. This is a Rust codebase.",
        ),
        scorer=haiku_grader(),
        sandbox="docker",
    )
