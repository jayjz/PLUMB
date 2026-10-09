# EXP-001 architecture

```text
data/cases/*.json ──┬──> direct model prompt ────> predictions.json ──┐
                    └──> structured prompt ────> predictions.json ───┤
data/gold/*.json ───────> evaluator only ──────────────────────────────┤
                                                                      v
                                                              scripts/score.py
```

Trust boundaries: (1) input records are untrusted content; (2) predicted findings are untrusted proposals, never commands; (3) labels and grading are independent of the model under evaluation; (4) human judgment is external to the experiment.

Python stdlib is sufficient to validate fixtures and score model outputs. Model integrations are intentionally not included: the baseline should remain provider-neutral and avoid unbudgeted inference. Model output cannot mutate cases or gold. Runs must capture provenance, prompt revision/hash, model ID/version, temperature/seed where supported, API pricing snapshot, token usage, elapsed time, predictions and scoring version; never assert deterministic model behavior without repeating runs.

Future architecture is conditional on evidence, not predetermined. Do not introduce a database, distributed queue, vector store, MCP service, UI, or agent framework in EXP-001.