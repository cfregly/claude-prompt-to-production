"""
OPTIONAL ACT 5 — Claude Agent SDK repo doctor
=============================================
Use this after Acts 1-4 if the interviewer asks, "Have you used Claude Code or
the Agent SDK directly?" It lets Claude inspect this repo, run tests, and propose
concrete improvements.

Run:
    python 05_agent_sdk_repo_doctor.py

Requires:
    pip install claude-agent-sdk
    export ANTHROPIC_API_KEY=...
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # the SDK's spawned CLI authenticates with ANTHROPIC_API_KEY from .env, like Acts 1-4

PROMPT = """
You are reviewing this demo repo for a technical founder audience.

Tasks:
1. Inspect the README and the four act scripts.
2. Run `python -m py_compile 01_first_call.py 02_agent_with_tools.py 03_evals.py 04_cost_engineering.py mcp_server/startup_metrics_server.py`.
3. Identify the top three changes that would make the demo clearer, safer, or more production-realistic.
4. Do not edit files unless you are certain the change is low-risk. Prefer a concise report.
5. Write the report plain: no em-dashes, no buzzwords, no 'it's not X, it's Y' framing.
   Verb-led sentences; numbers over adjectives.

Focus areas: tool descriptions as API contracts, eval coverage, prompt caching, model routing, cost accounting, and MCP portability.
""".strip()

async def main() -> None:
    try:
        from claude_agent_sdk import ClaudeAgentOptions, query
    except ImportError as exc:
        raise SystemExit(
            "Install the optional Agent SDK first: pip install claude-agent-sdk"
        ) from exc

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Grep", "Glob", "Bash", "Edit"],
        cwd=str(Path(__file__).resolve().parent),
    )
    try:
        async for message in query(prompt=PROMPT, options=options):
            if hasattr(message, "result") and message.result:
                print(message.result)
            else:
                print(message)
    except Exception as exc:  # noqa: BLE001
        # Some SDK/CLI version pairs mis-parse the terminal "success" message and
        # raise after the full report has streamed. Don't let a clean run die on
        # its last breath; re-raise anything that isn't that specific quirk.
        if "success" not in str(exc).lower():
            raise
        print("\n[note] run completed; ignored a terminal-message parsing quirk in the SDK/CLI pair")

if __name__ == "__main__":
    asyncio.run(main())
