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
│  inspect eval │────>│  Docker Sandbox               │
│  --model ...  │     │  ┌──────────────────────────┐ │
│               │<────│  │  Claude Code Agent        │ │
│  OpenRouter   │     │  │  - clones repo            │ │
│  ┌─────────┐  │     │  │  - reads prompt           │ │
│  │ Model X │  │     │  │  - edits code             │ │
│  └─────────┘  │     │  │  - runs cargo test        │ │
└─────────────┘     │  └──────────────────────────┘ │
                      └──────────────────────────────┘
                                    │
                      ┌─────────────v──────────────┐
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

# Create venv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
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
