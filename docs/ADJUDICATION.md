# EXP-002 adjudication and prediction contract

**All 30 keys are provisional. No independent qualified human review has occurred.** The user confirmed that no reviewer was available on 2026-10-09. Case authoring, source reading and mechanical checks by this assistant are not independent review, and no blinded manual audit is claimed.

## Label policy

An issue is an affected scope item plus the authorized commitment or unresolved decision, the draft passage (or complete omission search boundary), type, expected human action and rationale. The hidden `issue_id` identifies that issue for the evaluator; models never receive or guess it. Gold stores `identity.authorized_evidence` and `identity.proposal_evidence` as paragraph IDs, along with `expected_action`. Each positive has one target issue in this version.

- **Contradiction:** a proposal commits to an incompatible material/task/method relative to the approved record. Not an unaccepted supplier offer or merely historical disagreement.
- **Omission:** explicitly agreed work is missing from a proposal whose recorded scope boundary should include it. The keys cite every draft paragraph; absence from one paragraph is not proof of absence from the proposal. Some owners explicitly request separate listing, making bundled-work interpretations less likely.
- **Quantity:** the stated count, quantity or unit is incompatible with an approved measurement convention. Do not infer field accuracy, prices, structural adequacy or procurement waste from it.
- **Uncertainty:** the record leaves a necessary decision unresolved. Expected action is targeted clarification, not invented completion or forced contradiction. An already-flagged open question is still an uncertainty here; report this category separately.
- **Legitimate supersession:** an explicitly authorized revision resolves the historical difference; expected status `no_issue`, action `retain` in the key. A sample request does not authorize application until the subsequent approval.
- **No issue:** the draft aligns with authorized scope despite distractions. Exclusions may be correct.

The synthetic authority policy makes Owner the approving role; surveyor/supplier information alone does not amend scope. Actual contractual authority was not researched for fictional projects. Notes from unselected guide-specification alternatives are not imported as universal requirements. Material availability, genuine measurement quality, site condition veracity and all design/safety judgments remain unreviewed assumptions. Per-case `assumptions` and rationales expose these limitations.

## Blinded human review procedure

`data/exp002/review/sample_inputs.json` contains six allowlisted cases, one per category, with no keys, category labels, expected status, rationale or family metadata. It is an initial stratified sample, not a sufficient qualification of the whole dataset. `audit_status.json` records **pending**, with no invented answers or reviewers. Selection is deterministic; the author cannot become blind by re-reading their own inputs.

Recruit an independent estimator or construction contract reviewer with relevant scope-documentation experience. Supply the sample packet, prediction contract and original public source links; withhold keys and system outputs. Ask for: authorized scope, chronology, item-specific issues, exact evidence paragraphs, action, uncertain interpretations, source-note accuracy and plausible alternative readings. Have them record answers before revealing keys. Log qualifications, independence, dates, input/source hashes, disagreements and resolution. A second qualified reviewer should resolve contested labels. Audit the remaining 24 cases before treating the complete labels as independently reviewed. Do not tune prompts while resolving held-out labels. Changes require an amendment/new freeze; do not silently change gold after observing performance.

For future output adjudication, randomize condition names and output order, hide model identities, have reviewers assess entailment and action relevance against the record, and retain both judgments and disagreements. Include no-issue/abstention cases in manual review to detect missing gold issues. The executable semantic review format below concerns emitted findings only: it does not certify the gold or replace this broader audit.

## Strict predictions

A batch envelope contains **exactly** `dataset_version`, `input_sha256`, `predictions`. Each row contains **exactly** `case_id`, `status`, `reason`, `findings`. `status` is `issues`, `no_issue`, or `abstain`; only `issues` allows/requires a nonempty findings array. `reason` is nonempty text. Each finding contains exactly:

```json
{
  "type": "contradiction",
  "claim": "Name the scope item and supported incompatibility.",
  "action": "revise_proposal",
  "authorized_evidence": [{"pointer": "d3.p1", "quote": "Exact full paragraph from the input."}],
  "proposal_evidence": [{"pointer": "d5.p1", "quote": "Exact full draft paragraph from the input."}]
}
```

This is a shape example, not a valid case prediction. Allowed types are `contradiction`, `omission`, `quantity`, `uncertainty`. Only uncertainty uses `clarify`; the others use `revise_proposal`, a recommendation for human review. Supersession and clean are `no_issue` with an explanatory reason and `findings:[]`. Abstention is separately counted and never awarded correct-clearance credit.

The validator rejects unknown fields at every level, unknown/duplicate case IDs, nonexistent/wrong-role pointers, nonexact quotes, repeated evidence, duplicate finding identities (even with changed claim/type), nonfinite numbers, repeated JSON object keys, invalid enums and inconsistent statuses. Claims/reasons are bounded at 4,000 characters and findings at 20 per case. All requested cases are mandatory by default. `--allow-missing` explicitly retains missing cases with their missed issues and zero clearance credit. A malformed batch fails closed; it produces no favorable partial score. A later experiment must log invalid batches and evaluate a predeclared all-case fallback rather than discard failures.

The input hash is SHA-256 over the canonical JSON list of sorted allowlisted case inputs (UTF-8, sorted object keys, compact separators). The exporter prints it; a future runner wraps model rows with it. The dataset root hash is separate and covers frozen inputs, keys, provenance and prompts. Model attribution, raw responses, parse/retry failures, budgets and operator metadata belong in a separately frozen run manifest, not unvalidated extra prediction fields.

## Deterministic versus semantic grading

`score_exp002.py` matches **case + type + expected action + exact sets of authorized and proposal paragraph pointers**, one-to-one. A correct type on the wrong item is FP/FN, not a hit. Full exact quotes validate pointer content; they do not prove the claim. Broad citation bundles cannot receive identity credit. Empty/all-abstain predictions produce 20 missed issues on the entire dataset, including five clarification issues. Ten negatives include clean and supersession, reported separately by category.

Deterministic output is called **candidate localization**. It is deliberately not labeled model accuracy. A fabricated claim with correct anchors can still produce a candidate match, and a valid alternative citation can fail this strict proxy. Regression tests expose both the semantic limitation and the wrong-item defense. Per-case candidate issue IDs support audit. There is no fuzzy model judge, embedding judge or model-generated semantic truth.

An optional `--adjudication` JSON supplies exactly `prediction_sha256`, `dataset_sha256`, `reviewer_id`, `qualification`, `independent:true`, `qualified_human:true`, and `decisions`. Every emitted finding requires exactly one decision: `case_id`, integer `finding_index` (zero-based), boolean `supports_identity_and_action`, nonempty `rationale`. The prediction hash covers canonical JSON of the complete envelope; stale or incomplete review files are rejected. Semantic TP requires both an identity match and human support; unsupported candidates are FP and leave their gold issue missed. The code can validate a human attestation's shape and binding, **not authenticate expertise or honesty**. Test reviewers are explicitly fictional fixtures, not audit evidence.

Gold misses or reasonable alternative evidence spans should be logged separately. Do not expand acceptable test anchors after inspecting condition-specific outcomes. Review disagreements before unblinding; any label revision must be versioned and results clearly identified as revised exploratory analysis. Human-reviewed model findings against provisional gold still do not establish an independently validated benchmark.

## Historical EXP-001 verification

At baseline `9c47873`, C001 conflicts on treated/untreated framing; C003 on aluminum/vinyl railing; C004 omits agreed disposal; C002 correctly follows an authorized width revision; C005 aligns. All five are fictional with internally consistent provisional labels. C004's draft explicitly narrates that no disposal item is listed, making that case especially artificial. Other weaknesses: three positives/two negatives; short uniform inputs; no source provenance; shared author/labeler; no held-out partition; no quantity/ambiguity coverage; document-level rather than passage-level evidence; type-only matching and no semantic entailment. No model run or prior performance result was found. The original scorer and fixtures are retained byte-for-byte, including a regression demonstrating its wrong-item false credit. New results must never be mixed with its coarse scores.
