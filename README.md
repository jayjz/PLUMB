# PLUMB

**Know what's out of line.** A research-first scope-assurance tool for contractors.

PLUMB investigates a narrow question: **Can an assistant identify consequential contradictions and omissions between site-visit records and a proposal, cite the actual evidence, and appropriately abstain?**

**Status:** EXP-001 scaffold only. All five cases are fictional; no model evaluation, contractor pilot, customer discovery, pricing accuracy, or production usefulness is established.

## Start

Requires Python 3.11+; no API key or third-party dependencies for validation/scoring.

```bash
python -m unittest discover -s tests -v
python scripts/validate_cases.py
python scripts/score.py --predictions examples/empty_predictions.json
```

The final command demonstrates scoring with deliberately empty predictions; it is **not an AI baseline**. Read [the protocol](experiments/EXP-001.md) before any model comparison. To compare a model, use a frozen version of [prompts/direct.md](prompts/direct.md) or [prompts/structured.md](prompts/structured.md), supply ONLY `data/cases/*.json`, write a JSON file satisfying [the output contract](docs/CONTRACTS.md), and score it with `scripts/score.py`. Never supply `data/gold/` to the model.

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