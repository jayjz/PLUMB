# Experiment contracts

## Input
Each `data/cases/<id>.json` has `case_id`, `synthetic:true`, `scenario`, and ordered `documents`: `id`, `kind`, `timestamp` (ISO date), `author`, `text`. IDs are stable and unique. A later statement does **not** automatically override an earlier statement; explicit authorization and scope determine precedence.

## Findings
A model outputs exactly one prediction object per case:
```json
{"case_id":"C001","findings":[{"type":"contradiction","claim":"Framing material in proposal conflicts with approved request.","evidence":["visit","proposal"],"action":"Ask estimator to reconcile material before sending."}]}
```
Allowed `type`: `contradiction` or `omission`. `evidence` contains **document IDs** that appear in the case; quoting document text in `claim` is preferred. `findings:[]` is a valid no-issue response. No unsupported severity, confidence, cost, or invented prices. `action` must propose human verification, not direct modification or execution.

Predictions format:
```json
{"predictions":[{"case_id":"C001","findings":[]}]}
```
Provide all five case IDs exactly once; scoring rejects duplicates, unknown IDs, missing cases, invalid evidence pointers and malformed outputs.

## Gold
`data/gold/<id>.json` is evaluator-only. `issues` are typed with supporting `evidence`. Matching is per **case and issue type** for this small exploratory scaffold; avoid claiming detailed localization metrics from this coarse scoring. Evidence-pointer validity is separately reported, and valid IDs are not proof of correct support. Later evaluations must add blinded human adjudication of cited passages.

## Definition of contradiction
A material incompatibility between proposal content and the latest *authorized* record, not merely disagreement between two historical revisions. An omission is a requirement in the authorized record absent from a proposal expected to cover it. Clean and superseded cases prevent rewarding an always-flag strategy.