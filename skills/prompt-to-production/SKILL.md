---
name: prompt-to-production
description: >-
  Take a founder from a first Claude API call to an evaluated, cost-engineered
  agent in about 15 minutes: a streaming call with tokens and cost visible,
  tools as contracts, an eval harness (including honesty cases) wired into CI,
  cost engineering measured three ways (naive, cached, routed), and the same
  tools made portable over MCP. Use when someone wants to go from prompt to
  production, add evals to an AI product, cut an API bill, set up prompt
  caching or model routing, or build a first agent with tools and MCP. Triggers
  on "prompt to production", "add evals", "cut my API bill", "prompt caching",
  "model routing", "first agent", or "MCP server".
---

# prompt-to-production

The engineering discipline behind a Claude product: build the agent, gate it
with evals, measure the cost. AI startups stall in four places: the demo that
works once, the agent that breaks at the seams, the missing eval loop, and the
surprise bill. This skill walks all four in code you can extend.

## Workflow

### 1. First call
A streaming call with token and cost accounting visible from minute one.

### 2. Tools as contracts
Give the model hands. Tool descriptions are API contracts: exact semantics,
failure modes, return shape. Lint them with the agent-linter.

### 3. Evals before vibes
Run the golden cases, including two honesty cases where the pass condition is
saying "I don't have that" instead of inventing an answer. The act routes each
case across the model ladder by consequence and gates every tier on its own, so
every tier is proven before the cost table claims its savings, and it writes the
per-tier receipt to data/last_eval.md. Wire the gate into CI. The eval set is
also the retention instrument: the demo wins the trial, the eval set wins the
renewal.

### 4. Cost is architecture
Run the same workload three ways: naive, cached, routed. Prompt caching pays
for the shared context once. Model routing prices questions by consequence.
Measure it, do not assert it. A low per-interaction cost is also what lets a
startup give the product away as a growth lever.

### 5. MCP encore
Make the same tools portable over MCP for Claude Code and Desktop.

## What NOT to do
- Never quote someone else's cost numbers. Rerun the benchmark and quote your own.
- Never ship without the eval gate in CI.
- Never treat the API bill as a pricing problem when it is an architecture decision.
