# AI Compare - Model Comparison via Inspect AI + Claude Code

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an inspect-ai evaluation that compares different AI models by giving each one the same agentic coding task (clone a Rust repo, read a prompt, solve it) using Claude Code as the agent scaffold in a Docker sandbox, with models accessed via OpenRouter and results graded by Claude Haiku.

**Architecture:** inspect-ai orchestrates evaluations. Each eval run launches Claude Code inside a Docker container with Rust toolchain. The `sandbox_agent_bridge` intercepts Claude Code's API calls and routes them to whichever model inspect-ai is currently evaluating (via OpenRouter). A custom scorer reads a grading criteria markdown file and calls Haiku to grade the output. This lets us run the exact same agentic task across many models and compare results.

**Tech Stack:** Python 3.12+, inspect-ai, inspect-swe (for `claude_code()` solver), Docker, OpenRouter, Anthropic API (for grading)

---

## Project Structure

```
ai-compare/
├── README.md                        # Project overview and usage
├── pyproject.toml                   # Python project config + dependencies
├── .env.example                     # Environment variable template
├── compose.yaml                     # Docker compose for sandbox
├── Dockerfile                       # Sandbox image (Rust + Node.js)
├── tasks/
│   ├── __init__.py
│   └── clone_and_solve.py           # The inspect-ai task definition
├── prompts/
│   └── task_prompt.md               # Prompt the agent reads as instructions
├── grading/
│   └── grading_criteria.md          # Grading scheme (empty placeholder)
├── scorer/
│   ├── __init__.py
│   └── haiku_grader.py              # Custom scorer using Haiku
└── docs/
    └── plans/
        └── 2026-04-18-ai-compare.md # This file
```

---

### Task 1: Project Skeleton and Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `tasks/__init__.py`
- Create: `scorer/__init__.py`

**Step 1: Create `pyproject.toml`**

```toml
[project]
name = "ai-compare"
version = "0.1.0"
description = "Compare AI models on agentic coding tasks using inspect-ai and Claude Code"
requires-python = ">=3.12"
dependencies = [
    "inspect-ai>=0.3.52",
    "inspect-swe>=0.1.0",
    "anthropic>=0.42.0",
]

[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

**Step 2: Create `.env.example`**

```bash
# OpenRouter - used by inspect-ai to call models under evaluation
OPENROUTER_API_KEY=your-openrouter-api-key-here

# Anthropic - used by the grading scorer to call Haiku
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**Step 3: Create empty `__init__.py` files**

Create empty `tasks/__init__.py` and `scorer/__init__.py`.

**Step 4: Install dependencies**

Run: `pip install -e .`
Expected: Successful install of ai-compare and all dependencies.

**Step 5: Verify install**

Run: `python -c "import inspect_ai; print(inspect_ai.__version__)"`
Expected: Version number printed.

Run: `python -c "from inspect_swe import claude_code; print('ok')"`
Expected: `ok`

**Step 6: Commit**

```bash
git add pyproject.toml .env.example tasks/__init__.py scorer/__init__.py
git commit -m "chore: project skeleton with inspect-ai dependencies"
```

---

### Task 2: Docker Sandbox Environment

**Files:**
- Create: `Dockerfile`
- Create: `compose.yaml`

**Step 1: Create `Dockerfile`**

This image needs: Rust toolchain, git (for cloning), Node.js (required by Claude Code).

```dockerfile
FROM rust:1.87-bookworm

# Install Node.js (required by Claude Code agent)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
RUN mkdir -p /workspace
WORKDIR /workspace

CMD ["tail", "-f", "/dev/null"]
```

**Step 2: Create `compose.yaml`**

```yaml
services:
  default:
    build: .
    init: true
    command: tail -f /dev/null
    cpus: 2.0
    mem_limit: 4gb
```

**Step 3: Verify Docker build**

Run: `docker compose build`
Expected: Image builds successfully with Rust, Node.js, and git installed.

**Step 4: Verify toolchain in container**

Run: `docker compose run --rm default rustc --version`
Expected: Rust version output.

Run: `docker compose run --rm default node --version`
Expected: Node.js version output.

**Step 5: Clean up test containers**

Run: `docker compose down`

**Step 6: Commit**

```bash
git add Dockerfile compose.yaml
git commit -m "feat: Docker sandbox with Rust and Node.js for agentic evals"
```

---

### Task 3: Prompt and Grading Placeholder Files

**Files:**
- Create: `prompts/task_prompt.md`
- Create: `grading/grading_criteria.md`

**Step 1: Create `prompts/task_prompt.md`**

This is the prompt the agent reads as its task instructions. Use a realistic placeholder.

```markdown
# Task

You have been given a Rust codebase. Your job is to:

1. Read and understand the codebase structure
2. Run `cargo build` to verify it compiles
3. Run `cargo test` to see the current test results
4. Identify and fix any failing tests or compilation errors
5. Ensure all tests pass with `cargo test`

Report what you found and what you changed.
```

**Step 2: Create `grading/grading_criteria.md`**

This is intentionally empty - the grading scheme will be defined later.

```markdown
<!-- Grading criteria placeholder - define scoring rubric here -->
```

**Step 3: Commit**

```bash
git add prompts/task_prompt.md grading/grading_criteria.md
git commit -m "feat: add task prompt and grading criteria placeholder"
```

---

### Task 4: Custom Haiku Grader Scorer

**Files:**
- Create: `scorer/haiku_grader.py`
- Test: manual smoke test after Task 5

**Step 1: Write the scorer**

This scorer reads `grading/grading_criteria.md`, constructs a grading prompt, and calls Haiku to evaluate the agent's work.

```python
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


@scorer(metrics=[accuracy(), stderr()])
def haiku_grader():
    """Grade agent output using Claude Haiku with criteria from markdown file."""

    grading_criteria = GRADING_CRITERIA_PATH.read_text().strip()
    grader = get_model("anthropic/claude-haiku-4-5-20251001")

    async def score(state: TaskState, target: Target) -> Score:
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
            numeric = 1.0
        elif "PARTIAL" in completion:
            value = "P"
            numeric = 0.5
        else:
            value = "I"
            numeric = 0.0

        return Score(
            value=numeric,
            answer=state.output.completion,
            explanation=result.completion,
        )

    return score
```

**Step 2: Verify the file imports cleanly**

Run: `python -c "from scorer.haiku_grader import haiku_grader; print('ok')"`
Expected: `ok`

**Step 3: Commit**

```bash
git add scorer/haiku_grader.py
git commit -m "feat: custom Haiku-based scorer with external grading criteria"
```

---

### Task 5: The Main Inspect Task - Clone and Solve

**Files:**
- Create: `tasks/clone_and_solve.py`

**Step 1: Write the task**

This is the core task. It:
1. Defines a sample with a placeholder repo URL and setup script
2. The setup script clones the repo into the sandbox
3. The task prompt is read from `prompts/task_prompt.md`
4. Claude Code works on the codebase agentically
5. The Haiku scorer grades the result

```python
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
```

**Step 2: Verify the task is discoverable**

Run: `inspect list tasks tasks/clone_and_solve.py`
Expected: Shows `clone_and_solve` task.

**Step 3: Commit**

```bash
git add tasks/clone_and_solve.py
git commit -m "feat: clone-and-solve inspect task with Claude Code agent"
```

---

### Task 6: README

**Files:**
- Create: `README.md`

**Step 1: Write the README**

```markdown
# ai-compare

Compare AI models on agentic coding tasks using [Inspect AI](https://inspect.aisi.org.uk/) and Claude Code.

## How It Works

1. **Inspect AI** orchestrates the evaluation
2. **Claude Code** runs as the agent inside a Docker sandbox with Rust toolchain
3. The agent clones a repo, reads a task prompt, and works on the code
4. **Claude Haiku** grades the results against defined criteria
5. Models are swapped via **OpenRouter**, so you can compare any model on the same task

```
┌─────────────┐     ┌──────────────────────────────┐
│  inspect eval │────▶│  Docker Sandbox               │
│  --model ...  │     │  ┌──────────────────────────┐ │
│               │◀────│  │  Claude Code Agent        │ │
│  OpenRouter   │     │  │  - clones repo            │ │
│  ┌─────────┐  │     │  │  - reads prompt           │ │
│  │ Model X │  │     │  │  - edits code             │ │
│  └─────────┘  │     │  │  - runs cargo test        │ │
└─────────────┘     │  └──────────────────────────┘ │
                      └──────────────────────────────┘
                                    │
                      ┌─────────────▼──────────────┐
                      │  Haiku Grader               │
                      │  reads grading_criteria.md  │
                      │  scores agent output        │
                      └────────────────────────────┘
```

## Setup

### Prerequisites

- Python 3.12+
- Docker
- OpenRouter API key
- Anthropic API key (for grading)

### Install

```bash
# Clone this repo
git clone <this-repo-url>
cd ai-compare

# Install dependencies
pip install -e .

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configure

1. Set your repo URL in `tasks/clone_and_solve.py` (replace the `REPO_URL` placeholder)
2. Edit `prompts/task_prompt.md` with your task instructions
3. Define grading criteria in `grading/grading_criteria.md`

## Usage

### Run a single model

```bash
inspect eval tasks/clone_and_solve.py --model openrouter/anthropic/claude-sonnet-4-0
```

### Compare multiple models

```bash
# Run each model
inspect eval tasks/clone_and_solve.py --model openrouter/anthropic/claude-sonnet-4-0
inspect eval tasks/clone_and_solve.py --model openrouter/openai/gpt-4o
inspect eval tasks/clone_and_solve.py --model openrouter/google/gemini-2.5-pro

# View results
inspect view
```

### View results

```bash
# Launch the Inspect viewer
inspect view
```

## Project Structure

```
ai-compare/
├── tasks/clone_and_solve.py     # Inspect task definition
├── prompts/task_prompt.md       # Task instructions for the agent
├── grading/grading_criteria.md  # Grading rubric (read by scorer)
├── scorer/haiku_grader.py       # Custom Haiku-based scorer
├── Dockerfile                   # Sandbox image (Rust + Node.js)
├── compose.yaml                 # Docker compose config
└── .env.example                 # Environment variable template
```

## Adding New Tasks

1. Create a new prompt in `prompts/`
2. Create a new task file in `tasks/` following the pattern in `clone_and_solve.py`
3. Define grading criteria in `grading/`
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: project README with setup and usage instructions"
```

---

### Task 7: Smoke Test (End-to-End Verification)

**Files:**
- No new files

This task verifies the full pipeline works. You need real API keys and a real repo URL to run it.

**Step 1: Set environment variables**

Ensure `.env` has real values for `OPENROUTER_API_KEY` and `ANTHROPIC_API_KEY`. Source them:

Run: `source .env` (or `export` them manually)

**Step 2: Update the repo URL**

Edit `tasks/clone_and_solve.py` and replace `REPO_URL` with a real public Rust repo (e.g., a small repo with a known failing test).

**Step 3: Build the Docker image**

Run: `docker compose build`
Expected: Successful build.

**Step 4: Run the eval with a cheap model**

Run: `inspect eval tasks/clone_and_solve.py --model openrouter/anthropic/claude-haiku-4-5-20251001 --limit 1`
Expected: Eval runs, Claude Code agent activates in sandbox, clones repo, works on task, scorer grades output.

**Step 5: View results**

Run: `inspect view`
Expected: Browser opens with eval results showing the score and agent transcript.

**Step 6: Commit any fixes**

If anything needed adjusting during the smoke test, commit the fixes.

```bash
git add -u
git commit -m "fix: adjustments from smoke test"
```
