# claude-prompt-to-production

**Build the product.** A founder's 15-minute path from first Claude API call to an evaluated, cost-engineered agent. Measured live: $0.22 to $0.03 per task (−86%), 8 of 8 evals passing.

Most AI startups don't stall because the model is weak. They stall in one of four places:
the demo that works once, the agent that breaks at the seams, the eval loop that doesn't exist,
and the API bill that arrives like a plot twist. This repo is the 15-minute live build I run for
founders that walks through all four - in code you can extend, not slides you can forget.

Pair-built with Claude. That's not a disclaimer, it's the demo.

## Part of the Founder-to-Builder Activation Loop

This repo is **the engineering discipline**: build the agent, gate it with evals, measure the cost.
Its sibling, [`claude-startup-linter`](https://github.com/cfregly/claude-startup-linter), is **the strategy
instrument**: score a pitch, sharpen the path to product-market fit, answer platform risk, route the model. Diagnose the business there;
build and measure it here. A third sibling, [`claude-agent-linter`](https://github.com/cfregly/claude-agent-linter),
is **the interface discipline**: it lints MCP tool definitions into contract-grade shape - and it caught this very
repo's MCP server shipping empty parameter descriptions (docstrings don't reach the published schema. See
`mcp_server/startup_metrics_server.py`, now 100/100 after the fix). A fourth sibling,
[`claude-pitch-deck-linter`](https://github.com/cfregly/claude-pitch-deck-linter), is **the storytelling
discipline**: a Sequoia-arc deck builder and linter where every word fights for its place.

## The 15-minute arc

| Minute | File | The beat |
|---|---|---|
| 0-2 | `01_first_call.py` | First streaming call. See tokens and cost before minute three. |
| 2-6 | `02_agent_with_tools.py` | Give the model hands. Tool descriptions are API contracts. |
| 6-10 | `03_evals.py` | Evals before vibes - including two *honesty* cases. Wire it into CI. |
| 10-15 | `04_cost_engineering.py` | Same workload, 3 ways: naive vs cached vs routed. Measured, not asserted. |
| encore | `mcp_server/` | The same tools, made portable over MCP for Claude Code / Desktop. |
| optional | `05_agent_sdk_repo_doctor.py` | Claude Agent SDK scans this repo and proposes concrete improvements. |

## Quickstart

```bash
git clone https://github.com/cfregly/claude-prompt-to-production && cd claude-prompt-to-production
pip install -r requirements.txt
cp .env.example .env          # paste your key from console.anthropic.com

python 01_first_call.py
python 02_agent_with_tools.py
python 03_evals.py            # add --judge for an LLM judge on the honesty cases
python 04_cost_engineering.py --live
python 05_agent_sdk_repo_doctor.py   # optional Agent SDK act
```

No key yet? `python 04_cost_engineering.py` (without `--live`) renders the benchmark table from
clearly-labeled sample data so you can see the shape of the result first.

## The benchmark

`04_cost_engineering.py` runs 12 questions over a shared context block three ways (a ~5K-token shared prefix - deliberately above every current model's minimum cacheable prefix. Exact counts vary by tokenizer and model) and
prints cost, token accounting (fresh / cache-write / cache-read), and p50 latency per strategy.
Two levers, each about ten lines of code:

1. **Prompt caching** - cached input reads are ~90% off. The shared prefix gets paid for once.
2. **Model routing** - Haiku 4.5 ($1/$5 per MTok) for lookups, Sonnet 4.6 ($3/$15) for synthesis.
   The price spread across the model family is the cheapest performance optimization you'll ever ship.

### Cost is architecture, not accounting

Most startups discover their AI bill the way you discover a plot twist: after committing to the
story. The fix is not "negotiate pricing" - it's two architecture decisions, each about ten lines
of code, and you can measure them instead of arguing about them.

The experiment: the same 12 founder-FAQ questions over a shared ~5K-token context block, run
three ways. Latest live run (2026-06-10, models and pricing in `pricing.json`. Cache reads
engaged on all 24 cached calls):

| strategy | model | cost | p50 latency | vs naive |
|---|---|---|---|---|
| naive (Sonnet, no cache) | claude-sonnet-4-6 | $0.2196 | 2.39s | baseline |
| cached (Sonnet + prompt caching) | claude-sonnet-4-6 | $0.0585 | 2.26s | **-73%** |
| routed + cached (Haiku easy / Sonnet hard) | mixed | $0.0335 | 1.68s | **-85%** |

What each lever does:

- **Prompt caching** pays for the shared context once. The naive arm bought 67.5K fresh input
  tokens. The cached arm bought 36 - everything else was a ~90%-off cache read. You don't earn
  this by accident: the stable prefix has to be *bit-identical* across calls, which is an
  architecture decision about how you assemble prompts.
- **Model routing** prices questions by consequence. Lookups went to Haiku ($1/$5 per MTok),
  synthesis stayed on Sonnet ($3/$15). The model-family price spread is the cheapest performance
  optimization you will ever ship - and in this run it also cut p50 latency 30%, because the
  easy questions stopped waiting on a bigger model.

Reproducibility note: we ran this twice on the same day. Morning: -75% / -86% with flat latency.
Afternoon: -73% / -85% with faster latency. The costs agree within two points. The latency story
varies with load - which is exactly why this repo measures instead of asserts.

> Rerun it yourself: `python 04_cost_engineering.py --live` writes your numbers to
> `data/last_run.md` - quote your own run, never someone else's.

Pricing lives in [`pricing.json`](pricing.json) with a verify-before-quoting note. Rates move,
measurements don't lie.

## Ship responsibly

Two of the eight eval cases pass only when the agent says **"I don't have that."** An agent that
can decline gracefully is a feature you can sell to enterprises, not a benchmark penalty. Before
production: keep the eval gate in CI, log tool calls for auditability (Act 2 prints its trace),
and read Anthropic's [usage policies](https://www.anthropic.com/legal/aup) - trust is the actual
adoption unlock for startups selling into serious industries.

## Claude Skill

Packaged as a Claude Skill in [`skills/prompt-to-production/SKILL.md`](skills/prompt-to-production/SKILL.md). Upload it in Claude (Settings > Capabilities > Skills), then say "take me from prompt to production" or "add evals to my AI product." Claude walks the five acts: first call, tools as contracts, evals in CI, cost engineering, and the MCP encore.

## Go deeper

- [Claude Developer Platform docs](https://docs.claude.com) - start at tool use, prompt caching, and the Agent SDK
- [anthropics/claude-code](https://github.com/anthropics/claude-code) - the agentic coding tool this repo was pair-built with
- [anthropics/anthropic-cookbook](https://github.com/anthropics/anthropic-cookbook) and [anthropics/claude-quickstarts](https://github.com/anthropics/claude-quickstarts) - patterns to steal
- [anthropics/claude-agent-sdk-demos](https://github.com/anthropics/claude-agent-sdk-demos) - official Agent SDK patterns (pairs with Act 5)
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) - the MCP server ecosystem the encore plugs into

### Using the MCP encore with Claude Code / Desktop

```bash
claude mcp add startup-metrics -- python mcp_server/startup_metrics_server.py
```

or in `claude_desktop_config.json`:

```json
{ "mcpServers": { "startup-metrics": { "command": "python", "args": ["mcp_server/startup_metrics_server.py"] } } }
```

Then ask: *"What's our runway, and how's MRR trending?"* - same data as Act 2, zero app code.

## About

Built by [Chris Fregly](https://github.com/cfregly) - AI startup founder (PipelineAI), 3× O'Reilly
author, co-creator of DeepLearning.AI's *Generative AI with LLMs*, and organizer of meetup communities totaling 100K+ members worldwide (same-named chapters across cities) - current flagship:
[AI Performance Engineering](https://meetup.com/ai-performance-engineering), 370+ events. All company
data in `data/` is fictional. Find me at the meetup, on
[YouTube](https://youtube.com/@AIPerformanceEngineering), or most mornings at the 24/7 Corgi Cafe
in SF - founder office hours welcome.

MIT licensed. PRs welcome, especially new eval cases and routing strategies.

