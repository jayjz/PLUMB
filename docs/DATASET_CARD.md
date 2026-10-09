# EXP-002 dataset card

**Version:** `exp002-1.0.0-provisional`. **Status:** frozen research fixtures; all labels provisional and AI-authored. **Independent qualified human review: 0/30.** No model performance measurement has been made.

## Composition

| Category | Development | Held out | Total | Expected response |
|---|---:|---:|---:|---|
| Contradiction | 3 | 2 | 5 | Human review to revise proposal |
| Omission | 3 | 2 | 5 | Human review to include agreed work |
| Authorized supersession | 3 | 2 | 5 | No issue; retain authorized revision |
| Quantity/unit/measurement discrepancy | 3 | 2 | 5 | Human review to reconcile quantity |
| Unresolved ambiguity | 3 | 2 | 5 | Targeted clarification |
| Clean with distractions | 3 | 2 | 5 | No issue |
| **Total** | **18** | **12** | **30** | 20 issues, 10 negative controls |

The five original EXP-001 cases remain separate and unchanged; they are not counted here. The new cases have 4–5 chronological documents with individually addressable paragraphs: inquiry, observation, follow-up(s), measurement when needed, and draft. Five longer observation records contain administrative distractions. Supersession cases include successive amendments or sample requests followed by explicit approval. Opaque case IDs are shuffled relative to category and source. Shared document schemas and policy text remain a possible cue.

Source support comes from five UFGS guide specifications. All projects, people/roles, conversations, site facts, measurements, proposed errors, choices, revisions and keys are invented. Each case has `synthetic:true`, and so does every project document. Source notes are identified as factual paraphrases; they are not quotations, complete specifications or proof that the scenario occurred. Sources establish terminology and selected constraints only. No case is a documented field dispute. See [source discovery](DATASET_SOURCES.md).

## Partition and freeze

Development uses demolition, concrete walks and painting. Held out uses fencing and sheet metal; primary document hashes and source groups are disjoint. All six categories occur once in each source group, so category is not predictable from the source group alone. Thirty authored scenario families are separately named, but the more conservative dependence unit is **five source/trade groups**, only two in held out. Shared guide-specification style, institution and author remain confounders. This is not 30 statistically independent source families.

`data/exp002/index.json` records membership. `integrity.json` inventories every EXP-002 data/review/provenance file and frozen prompt, with SHA-256 and a canonical inventory root hash. Historical cases, keys, scorer, validator, tests, examples and EXP-001 prompts are separately byte-pinned. Do not refresh hashes in CI. A label/source/input correction requires a versioned amendment and a new freeze, with the previous artifact retained in Git history. If evaluation inputs informed tuning, demote them to development and recruit a fresh holdout; renaming a split does not restore blindness.

Held out means reserved for **future model/prompt selection**, not hidden from the author: this assistant authored and saw every key. Public repository storage cannot prevent a person or model operator from reading it, nor eliminate pretraining contamination from public specifications. Future inference must use isolated exported inputs, no repository access, no source browsing and no gold. Cases already exposed to a model in a previous experimental role must not be represented as unseen.

## Leakage and input boundaries

`python3 scripts/export_exp002.py --split held_out` reads only the index and selected case files, using an explicit nested allowlist. It exports neither index categories/families nor gold, rationales, issue IDs or reviewer files. Every condition receives identical source notes and chronological records. The operator's input hash covers canonical serialized inputs. The scorer rejects a prediction bundle with the wrong input hash. Hashes provide integrity, not access control; do not upload the repository or its gold directory.

Offline lexical screening compares record prose using five-word shingle Jaccard similarity (flag ≥0.35) and paragraphs of at least 20 words using three-word shingles (flag ≥0.85). Shared policy/source metadata are excluded from that similarity calculation but deliberately retained in model input. Cross-split source-group/family overlap and byte-identical source artifacts also fail validation. These thresholds detect copying, not subtle semantic templates; test coverage includes planted duplicates. Human review of near-duplicates and problem difficulty is pending.

## Intended use and limitations

Suitable for debugging evidence localization, chronology, strict output handling and a small prospective exploratory comparison. It is not an engineering benchmark, representative construction sample, field reliability estimate, product validation or proof of economic value. A qualified reviewer must check feasibility, correct source interpretation, authority assumptions, false negatives and label completeness before confirmatory claims. No real-world construction action should follow a fixture label.

Each positive case currently has one target issue; multi-issue behavior is covered only by evaluator regression fixtures. This makes issue identity easier than real proposal review. Some cases explicitly specify the measurement convention or a complete scope schedule to make the label identifiable. Source notes are short, inputs fit small contexts, handwriting/OCR and retrieval are absent, and explicit approvals may make the task easier than practice. Cases do not cover unavailable attachments, implicit contract incorporation or legally complex authority disputes. Ambiguity cases intentionally include drafts that already acknowledge pending decisions: clarification recall must be reported separately from defect detection and must not be sold as incremental defect discovery.

All assumptions are enumerated in each provisional key and in [adjudication](ADJUDICATION.md). No independent human review or blinded manual audit was possible in this run; the user confirmed that no reviewer was available. A gold-free sample packet and pending audit form are prepared for later use. Another AI reading a case would not change that status.
