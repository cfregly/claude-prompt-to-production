# claude-prompt-to-production

[![ci](https://github.com/cfregly/claude-prompt-to-production/actions/workflows/ci.yml/badge.svg)](https://github.com/cfregly/claude-prompt-to-production/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Build the product.** A founder's 15-minute path from first Claude API call to an evaluated, cost-engineered agent. Measured live: $0.22 to $0.03 per task (−86%), 8 of 8 evals passing.

Most AI startups don't stall because the model is weak. They stall in one of four places:
the demo that works once, the agent that breaks at the seams, the eval loop that doesn't exist,
and the API bill that nobody modeled until it landed. This repo is the 15-minute live build I run for
founders that walks through all four - in code you can extend, not slides you can forget.

Pair-built with Claude. That's not a disclaimer, it's the demo.

## Part of the Founder-to-Builder Activation Loop

This repo is **the engineering discipline**: build the agent, gate it with evals, measure the cost.
Its sibling, [`claude-startup-linter`](https://github.com/cfregly/claude-startup-linter), is **the strategy
instrument**: score a pitch, sharpen the path to product-market fit, answer platform risk, route the model. Diagnose the business there,
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

Most startups discover their AI bill only after they have committed to the
architecture. The fix is not "negotiate pricing" - it's two architecture decisions, each about ten lines
of code, and you can measure them instead of arguing about them.

The experiment: the same 12 founder-FAQ questions over a shared ~5K-token context block, run
three ways. Latest live run (2026-06-13, models and pricing in `pricing.json`. Cache reads
engaged on all 24 cached calls):

| strategy | model | cost | p50 latency | vs naive |
|---|---|---|---|---|
| naive (Sonnet, no cache) | claude-sonnet-4-6 | $0.2181 | 2.45s | baseline |
| cached (Sonnet + prompt caching) | claude-sonnet-4-6 | $0.0565 | 2.25s | **-74%** |
| routed + cached (Haiku easy / Sonnet hard) | mixed | $0.0313 | 1.85s | **-86%** |

What each lever does:

- **Prompt caching** pays for the shared context once. The naive arm bought 67.5K fresh input
  tokens. The cached arm bought 36 - everything else was a ~90%-off cache read. You don't earn
  this by accident: the stable prefix has to be *bit-identical* across calls, which is an
  architecture decision about how you assemble prompts.
- **Model routing** prices questions by consequence. Lookups went to Haiku ($1/$5 per MTok),
  synthesis stayed on Sonnet ($3/$15). The model-family price spread is the cheapest performance
  optimization you will ever ship - and in this run it also cut p50 latency 30%, because the
  easy questions stopped waiting on a bigger model.

Reproducibility note: these are the numbers committed in `data/last_run.md`. Re-running shifts the
cost by a point or two and the latency more, because latency moves with load, which is exactly why
this repo measures instead of asserts.

> Rerun it yourself: `python 04_cost_engineering.py --live` writes your numbers to
> `data/last_run.md` - quote your own run, never someone else's.

Pricing lives in [`pricing.json`](pricing.json) with a verify-before-quoting note. Rates move,
measurements don't lie.

## Lint the eval set: is it a moat, or a vibe?

Demos win the trial. Evals win the renewal. But an eval set is only a moat if it
tests what actually loses a customer. `eval_lint.py` scores a golden set the way
the linters score everything else, so you can gate the *quality of your evals* in
CI, not just the answers:

```bash
python eval_lint.py data/golden_set.jsonl    # the bundled set scores 97/100 (a moat)
python eval_lint.py --selftest               # the CI check
```

It fails a set with no honesty/refusal case (the only kind that catches a
confident hallucination), no adversarial case (nothing tries to break the
agent), or too few cases to be more than a vibe. The bundled golden set passes because it has all
three. A two-case, honesty-free set scores a C and tells you why.

## Ship responsibly

Two of the eight eval cases pass only when the agent says **"I don't have that."** An agent that
can decline gracefully is a feature you can sell to enterprises, not a benchmark penalty. Before
production: keep the eval gate in CI, log tool calls for auditability (Act 2 prints its trace),
and read Anthropic's [usage policies](https://www.anthropic.com/legal/aup) - trust is the actual
adoption unlock for startups selling into serious industries.

## Fork the starter and deploy your own

The five acts teach the moves. The [`starter/`](starter/) app is the minimal,
deployable skeleton you fork to ship your own product: a FastAPI service with one
Claude-backed endpoint and a one-file chat UI, ready to run locally or in a container.

```bash
pip install -r starter/requirements.txt
export ANTHROPIC_API_KEY=...        # from console.anthropic.com
uvicorn starter.app:app --reload    # open http://localhost:8000
```

Deploy it as a container anywhere that runs Docker:

```bash
docker build -f starter/Dockerfile -t claude-starter starter/
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY claude-starter
```

Run the commands above from the repo root. [`starter/README.md`](starter/README.md) has the
same flow plus one-command deploys for Fly.io and Render. The starter follows the same shape as
the official [anthropics/claude-quickstarts](https://github.com/anthropics/claude-quickstarts), a
minimal deployable Claude app you fork, with the eval and cost discipline from the repo root added
on top. No performance claims live in the starter: it is a skeleton to build on, and the numbers
above are what you measure once your workload is real.

## Claude Skill

Packaged as a Claude Skill in [`skills/prompt-to-production/SKILL.md`](skills/prompt-to-production/SKILL.md). Install it as a Claude Code plugin with `/plugin marketplace add cfregly/claude-prompt-to-production` then `/plugin install prompt-to-production@prompt-to-production-plugins`, or upload the `skills/prompt-to-production/` folder in the Claude app under Settings > Skills (see [Anthropic's skills guide](https://github.com/anthropics/skills)). Then say "take me from prompt to production" or "add evals to my AI product." Claude walks the five acts: first call, tools as contracts, evals in CI, cost engineering, and the MCP encore.

## Go deeper

- [Claude Developer Platform docs](https://docs.claude.com) - start at tool use, prompt caching, and the Agent SDK
- [anthropics/claude-code](https://github.com/anthropics/claude-code) - the agentic coding tool this repo was pair-built with
- [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) and [anthropics/claude-quickstarts](https://github.com/anthropics/claude-quickstarts) - patterns to steal
- [anthropics/claude-agent-sdk-demos](https://github.com/anthropics/claude-agent-sdk-demos) - official Agent SDK patterns (pairs with Act 5)
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) - the MCP server ecosystem the encore plugs into
- [Claude for Startups](https://claude.com/programs/startups) - credits and the highest rate limits once a founder is ready to ship on the first-party API

### Using the MCP encore with Claude Code / Desktop

```bash
claude mcp add startup-metrics -- python mcp_server/startup_metrics_server.py
```

or in `claude_desktop_config.json`:

```json
{ "mcpServers": { "startup-metrics": { "command": "python", "args": ["mcp_server/startup_metrics_server.py"] } } }
```

Then ask: *"What's our runway, and how's MRR trending?"* - same data as Act 2, zero app code.

## Limitations

This is a teaching scaffold, not a framework. The cost numbers come from one run
on one workload. Rerun on yours before quoting them. Pricing moves, so verify
against `pricing.json`. The eval set is small on purpose, to show the shape of
the gate, not to certify a model.

## About

Built by [Chris Fregly](https://github.com/cfregly) - AI startup founder (PipelineAI), 3× O'Reilly
author, co-creator of DeepLearning.AI's *Generative AI with LLMs*, and organizer of meetup communities totaling 100K+ members worldwide (same-named chapters across cities) - current flagship:
[AI Performance Engineering](https://meetup.com/ai-performance-engineering), 370+ events. All company
data in `data/` is fictional. Find me at the meetup, on
[YouTube](https://youtube.com/@AIPerformanceEngineering), or most mornings at the 24/7 Corgi Cafe
in SF - founder office hours welcome.

MIT licensed. PRs welcome, especially new eval cases and routing strategies.

