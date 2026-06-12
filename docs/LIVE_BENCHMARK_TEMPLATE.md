# Live benchmark paste template

After running:

```bash
python 04_cost_engineering.py --live
```

paste `data/last_run.md` below and commit it.

## Latest live benchmark

<PASTE TABLE HERE>

## One-line war story

I took the same 12-question context-heavy workload from `$BASELINE` to `$ROUTED_CACHED`, a `$PERCENT` reduction, while moving p50 latency from `$BASELINE_LATENCY` to `$ROUTED_LATENCY`. The levers were prompt caching, model routing, and eval-gated quality.
