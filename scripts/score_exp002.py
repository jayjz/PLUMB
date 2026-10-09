#!/usr/bin/env python3
"""Identity localization is deterministic; evidence entailment requires external adjudication."""
import argparse
import hashlib
import json
from pathlib import Path

from exp002 import (VERSION, ISSUE_TYPES, canonical, fields, nonempty, pointer_map,
                    read, require, serialize_case, validate, validate_pointers, verify_integrity)


def input_hash(cases):
    return hashlib.sha256(canonical([serialize_case(cases[c]) for c in sorted(cases)])).hexdigest()


def validate_predictions(obj, cases, allow_missing=False):
    fields(obj, 'dataset_version input_sha256 predictions', 'prediction bundle')
    require(obj['dataset_version']==VERSION, 'prediction version mismatch')
    require(obj['input_sha256']==input_hash(cases), 'wrong model input hash')
    require(isinstance(obj['predictions'], list), 'predictions must be array')
    found = {}
    for row in obj['predictions']:
        fields(row, 'case_id status reason findings', 'prediction')
        cid = row['case_id']
        require(isinstance(cid, str) and cid in cases and cid not in found, 'unknown/duplicate case ID')
        require(row['status'] in ('issues','no_issue','abstain'), 'invalid status')
        require(nonempty(row['reason']) and len(row['reason'])<=4000, 'reason required/too long')
        require(isinstance(row['findings'], list) and len(row['findings'])<=20, 'invalid findings')
        require(bool(row['findings'])==(row['status']=='issues'), 'inconsistent findings/status')
        signatures = set()
        for f in row['findings']:
            fields(f, 'type claim action authorized_evidence proposal_evidence', 'finding')
            require(isinstance(f['type'], str) and f['type'] in ISSUE_TYPES, 'invalid finding type')
            require(nonempty(f['claim']) and len(f['claim'])<=4000, 'claim required/too long')
            require(f['action'] in ('clarify','revise_proposal'), 'invalid action')
            require((f['type']=='uncertainty')==(f['action']=='clarify'), 'type/action mismatch')
            pm = pointer_map(cases[cid])
            for name, proposal in [('authorized_evidence',False),('proposal_evidence',True)]:
                evidence = f[name]
                require(isinstance(evidence,list) and bool(evidence), 'empty evidence')
                for ev in evidence:
                    fields(ev, 'pointer quote', 'evidence')
                    require(nonempty(ev['pointer']) and nonempty(ev['quote']), 'pointer/quote strings required')
                pointers = [e['pointer'] for e in evidence]
                validate_pointers(cases[cid], pointers, proposal, name)
                require(all(e['quote']==pm[e['pointer']][1] for e in evidence), 'quote is not exact full paragraph')
            signature = tuple(tuple(sorted(e['pointer'] for e in f[n])) for n in ('authorized_evidence','proposal_evidence'))
            require(signature not in signatures, 'duplicate finding identity (even with different type/claim)')
            signatures.add(signature)
        found[cid] = row
    require(allow_missing or set(found)==set(cases), 'missing case records')
    return found


def identity_matches(finding, issue):
    return (finding['type']==issue['type'] and finding['action']==issue['expected_action']
            and all({e['pointer'] for e in finding[n]}==set(issue['identity'][n])
                    for n in ('authorized_evidence','proposal_evidence')))


def adjudicate(review, obj, cases, dataset_hash):
    """Validate an external human attestation; software cannot certify qualifications."""
    fields(review, 'prediction_sha256 dataset_sha256 reviewer_id qualification independent qualified_human decisions', 'adjudication')
    require(review['prediction_sha256']==hashlib.sha256(canonical(obj)).hexdigest(), 'review prediction hash mismatch')
    require(nonempty(dataset_hash) and review['dataset_sha256']==dataset_hash, 'review dataset hash mismatch')
    require(review['independent'] is True and review['qualified_human'] is True, 'independent qualified human required')
    require(nonempty(review['reviewer_id']) and nonempty(review['qualification']), 'reviewer attribution required')
    require(isinstance(review['decisions'], list), 'review decisions array required')
    expected = {(r['case_id'], i) for r in obj['predictions'] for i in range(len(r['findings']))}
    decisions = {}
    for d in review['decisions']:
        fields(d, 'case_id finding_index supports_identity_and_action rationale', 'review decision')
        require(isinstance(d['case_id'],str) and type(d['finding_index']) is int, 'review key types')
        key = d['case_id'], d['finding_index']
        require(key in expected and key not in decisions, 'unknown/duplicate review finding')
        require(type(d['supports_identity_and_action']) is bool and nonempty(d['rationale']), 'review support/rationale required')
        decisions[key] = d['supports_identity_and_action']
    require(set(decisions)==expected, 'incomplete semantic review')
    return decisions


def score_batch(obj, cases, gold, allow_missing=False, review=None, dataset_hash=None):
    require(set(cases)==set(gold), 'evaluation cases and gold differ')
    predictions = validate_predictions(obj, cases, allow_missing)
    decisions = adjudicate(review,obj,cases,dataset_hash) if review is not None else None
    per_case = []
    for cid in sorted(cases):
        g = gold[cid]
        row = predictions.get(cid)
        findings = row['findings'] if row else []
        remaining = list(g['issues'])
        matched = []
        for i, f in enumerate(findings):
            # One-to-one consumption prevents duplicate credit; localization is only a candidate.
            hit = next((iss for iss in remaining if identity_matches(f,iss)), None)
            if hit is not None:
                matched.append({'finding_index':i, 'issue_id':hit['issue_id']})
                remaining.remove(hit)
        semantic_hits = (sum(decisions[(cid,m['finding_index'])] for m in matched)
                         if decisions is not None else None)
        per_case.append({'case_id':cid,'category':g['category'],'status':row['status'] if row else 'missing',
                         'gold_issues':len(g['issues']),'findings':len(findings),
                         'candidate_matches':matched,'candidate_tp':len(matched),
                         'candidate_fp':len(findings)-len(matched),'candidate_fn':len(remaining),
                         'semantic_tp':semantic_hits,
                         'explicit_correct_clearance':not g['issues'] and row is not None and row['status']=='no_issue'})
    tp = sum(r['candidate_tp'] for r in per_case)
    fp = sum(r['candidate_fp'] for r in per_case)
    fn = sum(r['candidate_fn'] for r in per_case)
    negatives = [r for r in per_case if not r['gold_issues']]
    semantic = None
    if decisions is not None:
        stp = sum(r['semantic_tp'] for r in per_case)
        sfp = sum(r['findings'] for r in per_case)-stp
        sfn = sum(r['gold_issues'] for r in per_case)-stp
        semantic = {'tp':stp,'fp':sfp,'fn':sfn,'precision':stp/(stp+sfp) if stp+sfp else None,
                    'recall':stp/(stp+sfn) if stp+sfn else None,
                    'status':'human_attested_prediction_review_against_provisional_labels'}
    by_category = {}
    for category in sorted({g['category'] for g in gold.values()}):
        subset = [r for r in per_case if r['category']==category]
        by_category[category] = {k:sum(r[k] for r in subset) for k in ('gold_issues','findings','candidate_tp','candidate_fp','candidate_fn','explicit_correct_clearance')}
        by_category[category]['cases'] = len(subset)
    return {'status':'localization_only' if review is None else 'human_attested_semantic_scoring',
            'warning':'Exact identity/action and valid quotations do not establish claim entailment. Synthetic labels remain provisional.',
            'dataset_sha256':dataset_hash,'input_sha256':obj['input_sha256'],
            'prediction_sha256':hashlib.sha256(canonical(obj)).hexdigest(),
            'expected_cases':len(cases),'received_cases':len(predictions),
            'missing_cases':sorted(set(cases)-set(predictions)),
            'abstentions':sum(r['status']=='abstain' for r in per_case),
            'candidate_localization':{'tp':tp,'fp':fp,'fn':fn,
                                      'precision':tp/(tp+fp) if tp+fp else None,
                                      'recall':tp/(tp+fn) if tp+fn else None},
            'semantic':semantic,
            'negative_case_count':len(negatives),
            'warnings_per_negative_case':sum(r['findings'] for r in negatives)/len(negatives) if negatives else None,
            'explicit_correct_clearances':sum(r['explicit_correct_clearance'] for r in negatives),
            'by_category':by_category,'per_case':per_case}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions',type=Path,required=True)
    parser.add_argument('--split',choices=['development','held_out'],required=True)
    parser.add_argument('--allow-missing',action='store_true',help='Retain missing cases in denominators; report them explicitly')
    parser.add_argument('--adjudication',type=Path)
    args=parser.parse_args()
    try:
        dataset_hash=verify_integrity()
        cases,gold,index,_=validate()
        ids={r['case_id'] for r in index['cases'] if r['split']==args.split}
        result=score_batch(read(args.predictions),{c:cases[c] for c in ids},{c:gold[c] for c in ids},
                           args.allow_missing,read(args.adjudication) if args.adjudication else None,dataset_hash)
    except (ValueError, KeyError, TypeError, OSError) as err:
        parser.error(str(err))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
