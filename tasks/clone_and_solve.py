from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_swe import claude_code

from scorer.haiku_grader import haiku_grader


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "task_prompt.md"

# Placeholder - replace with actual repo URL
REPO_URL = "https://github.com/OWNER/REPO.git"


def make_dataset() -> MemoryDataset:
    """Create the evaluation dataset with a single sample."""

    task_prompt = PROMPT_PATH.read_text().strip()

    return MemoryDataset([
        Sample(
            id="clone-and-solve",
            input=task_prompt,
            target="All tests pass. The agent should have identified issues, made fixes, and confirmed with cargo test.",
            setup=f"""#!/bin/bash
set -euo pipefail
cd /workspace
git clone {REPO_URL} repo
cd repo
echo "Repo cloned successfully"
""",
            metadata={
                "repo_url": REPO_URL,
            },
        )
    ])


@task
def clone_and_solve() -> Task:
    """Clone a Rust repo, read the task prompt, solve it with Claude Code."""
    return Task(
        dataset=make_dataset(),
        solver=claude_code(
            system_prompt="You are working in /workspace/repo. This is a Rust codebase.",
        ),
        scorer=haiku_grader(),
        sandbox="docker",
    )
