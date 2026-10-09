# Worklog

## 2026-10-09 — Initial scaffold
- Product hypothesis restricted to **review before sending a proposal**.
- EXP-001 defined with five *fictional* cases, direct and structured prompts, and separate evaluator-only labels.
- Python stdlib fixture checks + scorer and GitHub CI included.
- No model runs, customer data, interviews, field benchmarks or reported performance.
- Known limitation: scoring matches case and issue type, not exact semantic claim; human evidence review required.
- Next: verify CI and audit fixture correctness before freezing inputs, then record explicit model runs and provenance on a separate branch.