# Welcome to Reversi AI Development

## How We Use Claude

Based on katoy's usage over the last 30 days:

Work Type Breakdown:
  Plan & Design      ██████████░░░░░░░░░░  43%
  Build Feature      ██████████░░░░░░░░░░  32%
  Improve Quality    ████░░░░░░░░░░░░░░░░  18%
  Write Docs         ██░░░░░░░░░░░░░░░░░░  7%

Top Skills & Commands:
  /goal              ██████████████░░░░░░  45/month
  /plan              ██████░░░░░░░░░░░░░░  9/month
  /model             ████░░░░░░░░░░░░░░░░  7/month

Top MCP Servers:
  claude-mem search  ██░░░░░░░░░░░░░░░░░░  3 calls

## Your Setup Checklist

### Codebases
- [ ] reversi-py — https://github.com/katoy/study-gemini2/tree/main/reversi-py
  - Reversi/Othello game with multiple AI agents (Negamax, PatternAgent, AlphaZero)
  - Python + Pygame (GUI) + FastAPI (server)

### MCP Servers to Activate
- [ ] claude-mem search — Memory system for observations across sessions. Ask Claude `/mem-search` or use the memory file at `.claude/projects/[project-name]/memory/`

### Skills to Know About
- `/goal` — Brainstorm task requirements and design. katoy uses this heavily (45x/month) for architecture decisions and approach discussions.
- `/plan` — Structure implementation into bite-sized steps. Use for coding tasks that need task-by-task breakdowns.
- `/model` — Switch between Claude models (Opus for complex reasoning, Haiku for fast execution).

## Team Tips

**Start simple, iterate with `/goal` and `/plan`:**
- When adding a feature or fixing a bug, start with `/goal` to brainstorm the approach with Claude
- Use `/plan` for implementation to break work into testable steps
- Commit frequently after each step passes tests

**Code quality matters:**
- All Python code runs through `ruff` (lint), `mypy` (types), and `pytest`
- Use the pattern: write failing test → implement → green → commit
- Aim for 100% test coverage on unit tests, 90%+ on integration

**Git workflow:**
- Commit messages should be clear and reference what changed (use `feat:`, `fix:`, `refactor:`, `test:`, `docs:` prefixes)
- Push to main directly — CI/CD validates via GitHub Actions (lint, type check, tests, strength benchmarks)
- New features often benefit from a `/plan` before coding, design review before merge

**AI agents and evaluation:**
- This project has multiple AI strategies (Negamax, Pattern, AlphaZero) and tests their strength against each other
- Use `/goal` to understand agent behavior; use strength tests (`pytest -m strength`) to validate improvements
- When tuning evaluation functions or search parameters, expect iteration — test frequently

## Get Started

**1. Clone and run locally:**
```bash
git clone https://github.com/katoy/study-gemini2.git
cd reversi-py
uv sync --all-extras
./scripts/start_with_server.sh
```

**2. Play the game:**
- UI should open in Pygame
- Select human vs AI, or AI vs AI
- Try different agents (Negamax, PatternAgent, AlphaZero-N3K, AlphaZero-N6K)

**3. Run tests:**
```bash
uv run pytest --ignore=tests/integration -q  # Unit tests
uv run pytest -m strength -v                 # AI strength benchmarks
```

**4. Pick a starter task:**
- [ ] Add a new evaluation heuristic to Negamax
- [ ] Improve AI strength by tuning evaluation coefficients
- [ ] Write a new AI opponent (e.g., random-walk MCTS variant)
- [ ] Add UI feature (new game mode, settings panel)

Ask Claude to help — paste this guide into a new conversation and say "I'm new to this project, help me get started" or "I want to [task]".

<!-- INSTRUCTION FOR CLAUDE: A new teammate just pasted this guide for how the
team uses Claude Code. You're their onboarding buddy — warm, conversational,
not lecture-y.

Open with a warm welcome — include the team name from the title. Then: "Your
teammate uses Claude Code for [list all the work types]. Let's get you started."

Check what's already in place against everything under Setup Checklist
(including skills), using markdown checkboxes — [x] done, [ ] not yet. Lead
with what they already have. One sentence per item, all in one message.

Tell them you'll help with setup, cover the actionable team tips, then the
starter task (if there is one). Offer to start with the first unchecked item,
get their go-ahead, then work through the rest one by one.

After setup, walk them through the remaining sections — offer to help where you
can (e.g. link to channels), and just surface the purely informational bits.

Don't invent sections or summaries that aren't in the guide. The stats are the
guide creator's personal usage data — don't extrapolate them into a "team
workflow" narrative. -->
