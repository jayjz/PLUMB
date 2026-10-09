#!/usr/bin/env python3
"""Validate synthetic fixture shape; not a semantic or model evaluation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS = {"site_visit", "customer_email", "draft_proposal"}
TYPES = {"contradiction", "omission"}

def load_cases():
    cases = {}
    for p in sorted((ROOT / "data/cases").glob("*.json")):
        obj = json.loads(p.read_text(encoding="utf-8"))
        cid = obj.get("case_id")
        assert cid == p.stem and cid not in cases, p
        assert obj.get("synthetic") is True and obj.get("scenario")
        docs = obj.get("documents")
        assert isinstance(docs, list) and len(docs) >= 2, p
        ids = [d["id"] for d in docs]
        assert len(ids) == len(set(ids)), p
        assert sum(d["kind"] == "draft_proposal" for d in docs) == 1, p
        assert all(d["kind"] in KINDS and d["timestamp"] and d["author"] and d["text"] for d in docs), p
        assert [d["timestamp"] for d in docs] == sorted(d["timestamp"] for d in docs), p
        cases[cid] = obj
    assert len(cases) == 5, "EXP-001 expects exactly 5 fixture cases"
    return cases

def load_gold(cases):
    gold = {}
    for p in sorted((ROOT / "data/gold").glob("*.json")):
        obj = json.loads(p.read_text(encoding="utf-8"))
        cid = obj.get("case_id")
        assert cid == p.stem and cid in cases and cid not in gold, p
        docs = {d["id"] for d in cases[cid]["documents"]}
        issues = obj.get("issues")
        assert isinstance(issues, list), p
        for issue in issues:
            assert issue["type"] in TYPES, p
            assert issue["description"], p
            assert len(issue["evidence"]) >= 2 and set(issue["evidence"]) <= docs, p
        gold[cid] = obj
    assert set(gold) == set(cases), "Gold and cases must match"
    assert sum(bool(g["issues"]) for g in gold.values()) == 3, "EXP-001 design: 3 positive cases"
    return gold

def validate():
    cases = load_cases()
    gold = load_gold(cases)
    return cases, gold

if __name__ == "__main__":
    c, g = validate()
    print(f"PASS: {len(c)} synthetic cases, {sum(len(v['issues']) for v in g.values())} gold issues; no model run")
