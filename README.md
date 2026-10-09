# PLUMB

**Know what's out of line.** A research-first scope-assurance tool for contractors.

PLUMB investigates a narrow question: **Can an assistant identify consequential contradictions and omissions between site-visit records and a proposal, cite the actual evidence, and appropriately abstain?**

**Status:** EXP-002 research infrastructure: 30 source-informed synthetic cases (18 development / 12 held out), provisional keys and an identity-aware evaluator. Independent qualified human reviews: **0/30**. No model evaluation or performance claim. The original five EXP-001 cases and scorer are preserved.

## Start

Requires Python 3.11+; no API key or third-party dependencies for validation/scoring.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_cases.py
python3 scripts/score.py --predictions examples/empty_predictions.json
```

The final command is the **historical EXP-001 scorer**, which matches only issue type. It demonstrates scoring with deliberately empty predictions; it is **not an AI baseline**. Read [the protocol](experiments/EXP-001.md) before any model comparison. To compare a model, use a frozen version of [prompts/direct.md](prompts/direct.md) or [prompts/structured.md](prompts/structured.md), supply ONLY `data/cases/*.json`, write a JSON file satisfying [the output contract](docs/CONTRACTS.md), and score it with `scripts/score.py`. Never supply `data/gold/` to the model.

## EXP-002 workflow

```bash
python3 scripts/validate_exp002.py
python3 scripts/export_exp002.py --split development > /tmp/plumb-development.json
python3 scripts/export_exp002.py --split held_out > /tmp/plumb-held-out.json
# Only after an authorized, frozen experiment produces predictions:
python3 scripts/score_exp002.py --split held_out --predictions runs/predictions.json
# Authoring workspace only; verifies locally preserved original downloads:
python3 scripts/validate_exp002.py --source-cache runs/source-cache
```

Supply only exported `inputs` to a model. Never give it this repository, `data/gold/`, `data/exp002/gold/`, index metadata or reviewer files. Exact nested allowlists, input hashes, strict predictions, citation validation, duplicate/missing handling and frozen integrity checks support this boundary. Deterministic scores are **candidate localization**, not semantic correctness. Qualified independent human adjudication is separate and pending.

- [EXP-002 protocol](experiments/EXP-002.md): fair direct/structured comparison and future deterministic condition; no paid calls performed
- [Dataset card](docs/DATASET_CARD.md): counts, partitions, synthetic content and limitations
- [Sources](docs/DATASET_SOURCES.md): verified downloads, reuse boundaries, exclusions and access blockers
- [Adjudication and strict contract](docs/ADJUDICATION.md): provisional labels, evidence identity, audit packet and human review

Original public specification PDFs are retained locally, not redistributed; Git contains their hashes and original factual notes. CI checks repository integrity without claiming to reverify remote PDFs. The dataset is not yet an independently validated benchmark, and the future hybrid model condition is not implemented.

## Boundaries

No autonomous construction advice, prices, quantities, structural or code compliance judgments. Every finding is a review suggestion requiring qualified human confirmation. Records and labels are synthetic; don't claim field validity. Preserve immutable experiment artifacts and distinguish observed results from hypotheses.

## Navigation

- [AGENTS.md](AGENTS.md): rules for coding agents and contributors
- [docs/PRODUCT.md](docs/PRODUCT.md): buyer/job hypothesis, exclusions, commercial gates
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): minimal design, trust boundaries
- [docs/CONTRACTS.md](docs/CONTRACTS.md): typed records and model predictions
- [experiments/EXP-001.md](experiments/EXP-001.md): preregistered exploratory study
- [docs/WORKLOG.md](docs/WORKLOG.md): decisions/status and next steps
- [docs/SOURCES.md](docs/SOURCES.md): technical/methodological references

Copyright remains with respective owners for external sources; fixtures here are original fictional examples. No license has been selected yet; do not assume reuse permissions.