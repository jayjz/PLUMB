#!/usr/bin/env python3
"""EXP-002 data contracts and allowlisted serialization; Python stdlib only."""
import hashlib
import json
import re
from collections import Counter
from datetime import date
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/exp002'
VERSION = 'exp002-1.0.0-provisional'
CATEGORIES = {'contradiction', 'omission', 'supersession', 'quantity', 'uncertainty', 'clean'}
ISSUE_TYPES = CATEGORIES - {'supersession', 'clean'}
KINDS = {'customer_inquiry', 'site_observation', 'follow_up', 'measurement', 'draft_proposal'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(obj, names, where):
    require(isinstance(obj, dict) and set(obj) == set(names.split()), f'{where}: unexpected/missing fields')


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def unique_strings(value, where, allow_empty=False):
    require(isinstance(value, list) and (allow_empty or bool(value)), f'{where}: expected array')
    require(all(nonempty(x) for x in value), f'{where}: strings required')
    require(len(value) == len(set(value)), f'{where}: duplicates')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON key: {key}')
        result[key] = value
    return result


def loads(text):
    def reject(value):
        raise ValueError(f'non-finite JSON number: {value}')
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=reject)


def read(path):
    return loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def pointer_map(case):
    return {f"{d['id']}.{p['id']}": (d['kind'], p['text'])
            for d in case['documents'] for p in d['paragraphs']}


def validate_pointers(case, pointers, proposal, where):
    unique_strings(pointers, where)
    table = pointer_map(case)
    require(all(p in table for p in pointers), f'{where}: nonexistent paragraph')
    require(all((table[p][0] == 'draft_proposal') == proposal for p in pointers),
            f'{where}: wrong document role')


def serialize_case(case):
    """Never copy entire objects: added evaluator-only fields cannot cross this boundary."""
    return {
        'dataset_version': VERSION,
        **{k: case[k] for k in ('case_id', 'synthetic', 'title', 'authority_policy')},
        'source_context': [{k: s[k] for k in ('source_id', 'url', 'document_identity', 'section',
                                            'pdf_page', 'note', 'use')}
                           for s in case['source_context']],
        'documents': [{**{k: d[k] for k in ('id', 'kind', 'timestamp', 'author', 'synthetic')},
                       'paragraphs': [{k: p[k] for k in ('id', 'text')} for p in d['paragraphs']]}
                      for d in case['documents']],
    }


def load_inputs(split, base=DATA):
    """Input path reads index and selected cases ONLY. No gold or directory context."""
    require(split in {'development', 'held_out'}, 'unknown split')
    index = read(base / 'index.json')
    require(index['dataset_version'] == VERSION, 'wrong dataset version')
    ids = [r['case_id'] for r in index['cases'] if r['split'] == split]
    require(all(re.fullmatch(r'E\d{3}', cid) for cid in ids), 'unsafe case ID')
    return [serialize_case(read(base / 'cases' / f'{cid}.json')) for cid in sorted(ids)]


def shingles(case):
    # Exclude shared instructions and source notes; compare the actual project record prose.
    words = re.findall(r'\w+', ' '.join(p['text'].lower() for d in case['documents']
                                      for p in d['paragraphs']))
    return {tuple(words[i:i+5]) for i in range(len(words)-4)}


def leakage_report(cases, rows):
    rowmap = {r['case_id']: r for r in rows}
    sets = {cid: shingles(c) for cid, c in cases.items()}
    pairs = []
    for a, b in combinations(sorted(cases), 2):
        union = sets[a] | sets[b]
        j = len(sets[a] & sets[b]) / len(union) if union else 1.0
        pairs.append({'a': a, 'b': b, 'jaccard_5gram': round(j, 6),
                      'cross_split': rowmap[a]['split'] != rowmap[b]['split']})
    suspicious = [p for p in pairs if p['jaccard_5gram'] >= 0.35]
    # Catch a copied paragraph even inside otherwise unrelated long cases.
    paragraph_hits = []
    for a, b in combinations(sorted(cases), 2):
        pa = [re.findall(r'\w+', p['text'].lower()) for d in cases[a]['documents'] for p in d['paragraphs']]
        pb = [re.findall(r'\w+', p['text'].lower()) for d in cases[b]['documents'] for p in d['paragraphs']]
        for x in pa:
            for y in pb:
                if min(len(x), len(y)) < 20:
                    continue
                sx = {tuple(x[i:i+3]) for i in range(len(x)-2)}
                sy = {tuple(y[i:i+3]) for i in range(len(y)-2)}
                if len(sx & sy) / len(sx | sy) >= 0.85:
                    paragraph_hits.append({'a': a, 'b': b})
    dev = [r for r in rows if r['split'] == 'development']
    held = [r for r in rows if r['split'] == 'held_out']
    overlap = {k: sorted({r[k] for r in dev} & {r[k] for r in held})
               for k in ('family', 'source_group')}
    return {'threshold_case': 0.35, 'threshold_paragraph': 0.85,
            'max_pair': max(pairs, key=lambda p: p['jaccard_5gram']) if pairs else None,
            'flagged_pairs': suspicious, 'copied_paragraphs': paragraph_hits,
            'cross_split_overlap': overlap,
            'limitation': 'Lexical screening and authored family IDs cannot prove semantic independence or absence of pretraining contamination.'}


def validate(base=DATA):
    index = read(base / 'index.json')
    fields(index, 'dataset_version status case_count cases', 'index')
    require(index['dataset_version'] == VERSION and index['case_count'] == 30, 'version/count mismatch')
    rows = index['cases']
    require(isinstance(rows, list) and len(rows) == 30, '30 index rows required')
    cases, gold = {}, {}
    for r in rows:
        fields(r, 'case_id split category family source_group', 'index row')
        cid = r['case_id']
        require(isinstance(cid, str) and re.fullmatch(r'E\d{3}', cid) and cid not in cases, 'invalid/duplicate case ID')
        require(r['split'] in {'development', 'held_out'} and r['category'] in CATEGORIES, 'invalid partition/category')
        require(nonempty(r['family']) and nonempty(r['source_group']), 'missing grouping')
        c = read(base / 'cases' / f'{cid}.json')
        fields(c, 'case_id synthetic title authority_policy source_context documents', cid)
        require(c['case_id'] == cid and c['synthetic'] is True, f'{cid}: case identity/synthetic')
        require(nonempty(c['title']) and nonempty(c['authority_policy']), f'{cid}: missing context')
        docs = c['documents']
        require(isinstance(docs, list) and len(docs) >= 4, f'{cid}: insufficient chronology')
        dids, dates, kinds = [], [], []
        for d in docs:
            fields(d, 'id kind timestamp author synthetic paragraphs', cid)
            require(isinstance(d['id'], str) and re.fullmatch(r'd\d+', d['id']), 'invalid doc ID')
            require(d['kind'] in KINDS and d['synthetic'] is True and nonempty(d['author']), 'invalid doc metadata')
            require(isinstance(d['timestamp'], str), 'date must be string')
            dates.append(date.fromisoformat(d['timestamp']))
            dids.append(d['id']); kinds.append(d['kind'])
            require(isinstance(d['paragraphs'], list) and bool(d['paragraphs']), 'empty paragraphs')
            pids = []
            for p in d['paragraphs']:
                fields(p, 'id text', 'paragraph')
                require(isinstance(p['id'], str) and re.fullmatch(r'p\d+', p['id']) and nonempty(p['text']), 'invalid paragraph')
                pids.append(p['id'])
            require(len(pids) == len(set(pids)), 'duplicate paragraph ID')
        require(len(dids) == len(set(dids)) and dates == sorted(dates), 'duplicate doc IDs/unordered dates')
        require(kinds.count('draft_proposal') == 1 and kinds[-1] == 'draft_proposal', 'proposal boundary')
        require({'customer_inquiry', 'site_observation', 'follow_up'} <= set(kinds), 'missing record kinds')
        require(isinstance(c['source_context'], list) and bool(c['source_context']), 'no provenance')
        for s in c['source_context']:
            fields(s, 'source_id url document_identity section pdf_page note use', 'source context')
            require(s['source_id'] == r['source_group'], 'source group mismatch')
            require(all(nonempty(s[k]) for k in ('url','document_identity','section','note','use')), 'source context empty')
            require(type(s['pdf_page']) is int and s['pdf_page'] > 0, 'invalid page')
        g = read(base / 'gold' / f'{cid}.json')
        fields(g, 'case_id category review_status independent_human_review expected_status issues resolution assumptions', 'gold')
        require(g['case_id'] == cid and g['category'] == r['category'], 'gold identity/category')
        require(g['review_status'] == 'provisional_ai_authored' and g['independent_human_review'] is False, 'unsupported review claim')
        require(g['expected_status'] == ('issues' if r['category'] in ISSUE_TYPES else 'no_issue'), 'gold status')
        unique_strings(g['assumptions'], 'assumptions')
        require(isinstance(g['issues'], list), 'issues must be list')
        require(len(g['issues']) == (1 if r['category'] in ISSUE_TYPES else 0), 'unexpected issue count')
        for issue in g['issues']:
            fields(issue, 'issue_id type expected_action identity rationale', 'issue')
            require(issue['issue_id'] == cid+'-01' and issue['type'] == r['category'], 'issue identity')
            require(issue['expected_action'] == ('clarify' if issue['type']=='uncertainty' else 'revise_proposal'), 'action mismatch')
            require(nonempty(issue['rationale']), 'empty rationale')
            fields(issue['identity'], 'authorized_evidence proposal_evidence', 'identity')
            validate_pointers(c, issue['identity']['authorized_evidence'], False, 'gold source')
            validate_pointers(c, issue['identity']['proposal_evidence'], True, 'gold proposal')
            if issue['type'] == 'omission':
                require(set(issue['identity']['proposal_evidence']) == {p for p,(k,_) in pointer_map(c).items() if k=='draft_proposal'}, 'omission must search entire proposal')
        res = g['resolution']
        fields(res, 'type expected_action authorized_evidence proposal_evidence rationale', 'resolution')
        expected_type = 'legitimate_supersession' if r['category']=='supersession' else 'no_issue' if r['category']=='clean' else r['category']
        require(res['type']==expected_type and nonempty(res['rationale']), 'resolution type/rationale')
        require(res['expected_action']==('retain' if not g['issues'] else g['issues'][0]['expected_action']), 'resolution action')
        validate_pointers(c, res['authorized_evidence'], False, 'resolution source')
        validate_pointers(c, res['proposal_evidence'], True, 'resolution proposal')
        if g['issues']:
            require(all(res[k]==g['issues'][0]['identity'][k] for k in ('authorized_evidence','proposal_evidence')), 'resolution evidence mismatch')
        cases[cid], gold[cid] = c, g
    require({p.stem for p in (base/'cases').glob('*.json')} == set(cases), 'unexpected/missing case file')
    require({p.stem for p in (base/'gold').glob('*.json')} == set(gold), 'unexpected/missing gold file')
    require(Counter(r['category'] for r in rows) == Counter({c:5 for c in CATEGORIES}), 'category balance')
    for split, n in [('development',3),('held_out',2)]:
        require(Counter(r['category'] for r in rows if r['split']==split) == Counter({c:n for c in CATEGORIES}), 'split balance')
    sources = read(base / 'sources/manifest.json')['sources']
    smap = {}
    for s in sources:
        require(s['source_id'] not in smap, 'duplicate source')
        for k in ('url','publisher','access_date','document_identity','content_type','status'):
            require(nonempty(s[k]), f'source lacks {k}')
        date.fromisoformat(s['access_date'])
        require(s['url'].startswith('https://') and isinstance(s['artifacts'], list), 'bad source metadata')
        require(nonempty(s['reuse']['basis']) and s['reuse']['redistribute_original'] is False, 'source reuse boundary')
        require(bool(s['artifacts']) or nonempty(s.get('reason')), 'missing artifact explanation')
        for a in s['artifacts']:
            require(re.fullmatch(r'[\da-f]{64}', a['sha256']) is not None and type(a['bytes']) is int and a['bytes']>0, 'invalid source hash/size')
            require(Path(a['cache_path']).name==a['cache_path'] and a['redistributed'] is False, 'unsafe source path')
        smap[s['source_id']] = s
    for r in rows:
        s = smap[r['source_group']]
        require(s['status']=='used_factual_notes_only' and s['partition']==r['split'] and bool(s['artifacts']), 'unverified/shared primary source')
        note_path = Path(s['notes_path'])
        require(note_path.parts[:4]==('data','exp002','sources','notes') and '..' not in note_path.parts, 'unsafe notes path')
        notes = read(base / 'sources/notes' / note_path.name)
        for sc in cases[r['case_id']]['source_context']:
            require(sc['url']==s['url'] and sc['document_identity']==s['document_identity'], 'source citation mismatch')
            require({'section':sc['section'],'pdf_page':sc['pdf_page'],'note':sc['note']} in notes['sections'], 'untraceable source note')
    leakage = leakage_report(cases, rows)
    require(not leakage['flagged_pairs'] and not leakage['copied_paragraphs'], 'near-duplicate cases')
    require(not any(leakage['cross_split_overlap'].values()), 'partition leakage')
    # Byte-identical source artifacts cannot evade partition isolation by aliasing IDs.
    devhash = {a['sha256'] for s in sources if s.get('partition')=='development' for a in s['artifacts']}
    heldhash = {a['sha256'] for s in sources if s.get('partition')=='held_out' for a in s['artifacts']}
    require(not devhash & heldhash, 'source artifact overlaps partitions')
    return cases, gold, index, leakage


def inventory(root=ROOT):
    paths = list((root/'data/exp002').rglob('*')) + list((root/'prompts/exp002').glob('*'))
    return {str(p.relative_to(root)): digest(p) for p in sorted(paths)
            if p.is_file() and p.name != 'integrity.json'}


def verify_integrity(root=ROOT):
    frozen = read(root/'data/exp002/integrity.json')
    require(frozen['dataset_version']==VERSION, 'integrity version')
    require(frozen['files']==inventory(root), 'frozen inventory/hash mismatch; investigate, do not auto-refreeze')
    for path, expected in frozen['historical_files'].items():
        require(digest(root/path)==expected, f'historical artifact changed: {path}')
    require(hashlib.sha256(canonical(frozen['files'])).hexdigest()==frozen['dataset_sha256'], 'dataset root hash mismatch')
    return frozen['dataset_sha256']


def verify_source_cache(cache, base=DATA):
    checked = 0
    for s in read(base/'sources/manifest.json')['sources']:
        for a in s['artifacts']:
            p = Path(cache)/a['cache_path']
            require(p.is_file() and digest(p)==a['sha256'] and p.stat().st_size==a['bytes'], f'source cache mismatch: {p}')
            checked += 1
    return checked
