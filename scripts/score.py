#!/usr/bin/env python3
"""Simple exploratory scorer. Matches issue type within case; no semantic claim grading."""
import argparse
import json
from pathlib import Path
from validate_cases import validate, TYPES

def score(obj):
    cases, gold = validate()
    rows = obj.get("predictions")
    if not isinstance(rows, list) or len(rows) != len(cases):
        raise ValueError("Provide exactly one prediction per case")
    ids = [r.get("case_id") for r in rows if isinstance(r, dict)]
    if len(ids) != len(rows) or set(ids) != set(cases) or len(set(ids)) != len(ids):
        raise ValueError("Prediction case IDs missing, duplicated or unexpected")
    tp = fp = fn = evidence_total = valid_pointer_total = 0
    clean_warnings = 0
    per_case = []
    for row in rows:
        cid = row["case_id"]
        findings = row.get("findings")
        if not isinstance(findings, list):
            raise ValueError(f"{cid}: findings must be an array")
        document_ids = {d["id"] for d in cases[cid]["documents"]}
        pred_types = []
        for f in findings:
            if not isinstance(f, dict) or f.get("type") not in TYPES or not isinstance(f.get("claim"), str) or not f["claim"].strip() or not isinstance(f.get("action"), str) or not f["action"].strip():
                raise ValueError(f"{cid}: malformed finding")
            ev = f.get("evidence")
            if not isinstance(ev, list) or not ev or not all(isinstance(x, str) for x in ev):
                raise ValueError(f"{cid}: invalid evidence list")
            if len(ev) != len(set(ev)) or not set(ev) <= document_ids:
                raise ValueError(f"{cid}: evidence must be unique, real document IDs")
            evidence_total += len(ev)
            valid_pointer_total += len(ev)
            pred_types.append(f["type"])
        expected = [i["type"] for i in gold[cid]["issues"]]
        remaining = expected[:]
        hit = 0
        for pred in pred_types:
            if pred in remaining:
                remaining.remove(pred)
                hit += 1
        t, p, n = hit, len(pred_types) - hit, len(remaining)
        tp += t; fp += p; fn += n
        if not expected:
            clean_warnings += len(findings)
        per_case.append({"case_id":cid,"tp":t,"fp":p,"fn":n,"warnings":len(findings)})
    return {
        "status":"exploratory_scoring_only",
        "warning":"Matching uses issue type only, not semantic claim correctness; valid IDs do not establish evidence support.",
        "cases":len(cases),"tp":tp,"fp":fp,"fn":fn,
        "precision":tp/(tp+fp) if tp+fp else None,
        "recall":tp/(tp+fn) if tp+fn else None,
        "false_warnings_per_clean_case":clean_warnings / sum(not x["issues"] for x in gold.values()),
        "evidence_pointer_validity":valid_pointer_total / evidence_total if evidence_total else None,
        "per_case":sorted(per_case,key=lambda row:row["case_id"])
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = score(json.loads(args.predictions.read_text(encoding="utf-8")))
    except (ValueError, AssertionError, KeyError, TypeError) as err:
        parser.error(str(err))
    print(json.dumps(result, indent=2))
