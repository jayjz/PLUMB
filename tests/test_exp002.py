import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from exp002 import (DATA, VERSION, canonical, digest, inventory, leakage_report, load_inputs,
                    loads, pointer_map, read, serialize_case, validate, verify_integrity,
                    verify_source_cache)
from score_exp002 import input_hash, score_batch, validate_predictions


class EXP002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases,cls.gold,cls.index,cls.leakage=validate()
        cls.positive=next(c for c,g in cls.gold.items() if g['category']=='contradiction')

    def bundle(self, cases=None):
        cases=cases or self.cases
        return {'dataset_version':VERSION,'input_sha256':input_hash(cases),'predictions':[
            {'case_id':c,'status':'abstain','reason':'Fixture abstention, not a model run.','findings':[]}
            for c in sorted(cases)]}

    def finding(self,cid=None):
        cid=cid or self.positive
        issue=self.gold[cid]['issues'][0]
        pm=pointer_map(self.cases[cid])
        return {'type':issue['type'],'claim':'Fixture claim requires independent semantic review.',
                'action':issue['expected_action'],**{
                n:[{'pointer':p,'quote':pm[p][1]} for p in issue['identity'][n]]
                for n in ('authorized_evidence','proposal_evidence')}}

    def positive_bundle(self):
        obj=self.bundle()
        row=next(r for r in obj['predictions'] if r['case_id']==self.positive)
        row.update(status='issues',findings=[self.finding()])
        return obj,row

    def review(self,obj,accepted=True):
        return {'prediction_sha256':hashlib.sha256(canonical(obj)).hexdigest(),
                'dataset_sha256':'fixture-dataset-hash','reviewer_id':'TEST-ONLY-NOT-A-REAL-REVIEWER',
                'qualification':'test fixture only','independent':True,'qualified_human':True,
                'decisions':[{'case_id':r['case_id'],'finding_index':i,
                              'supports_identity_and_action':accepted,'rationale':'Test decision only.'}
                             for r in obj['predictions'] for i in range(len(r['findings']))]}

    def test_balance_and_provisional_status(self):
        self.assertEqual(len(self.cases),30)
        self.assertEqual(sum(len(g['issues']) for g in self.gold.values()),20)
        self.assertTrue(all(g['independent_human_review'] is False for g in self.gold.values()))
        self.assertFalse(self.leakage['flagged_pairs'])

    def test_frozen_integrity(self):
        self.assertEqual(len(verify_integrity()),64)

    def test_abstention_not_clean_credit(self):
        result=score_batch(self.bundle(),self.cases,self.gold)
        self.assertEqual(result['candidate_localization'],{'tp':0,'fp':0,'fn':20,'precision':None,'recall':0.0})
        self.assertEqual(result['explicit_correct_clearances'],0)
        self.assertEqual(result['abstentions'],30)
        self.assertIsNone(result['semantic'])

    def test_type_only_wrong_identity_not_credited(self):
        obj,row=self.positive_bundle()
        pm=pointer_map(self.cases[self.positive])
        f=row['findings'][0]
        wrong=next(p for p,(kind,_) in pm.items() if kind!='draft_proposal' and p not in self.gold[self.positive]['issues'][0]['identity']['authorized_evidence'])
        f['authorized_evidence']=[{'pointer':wrong,'quote':pm[wrong][1]}]
        result=score_batch(obj,self.cases,self.gold)
        self.assertEqual(result['candidate_localization']['tp'],0)
        self.assertEqual(result['candidate_localization']['fp'],1)
        self.assertEqual(result['candidate_localization']['fn'],20)

    def test_correct_anchors_are_only_candidates(self):
        obj,row=self.positive_bundle()
        row['findings'][0]['claim']='The owner approved a moon landing.'
        result=score_batch(obj,self.cases,self.gold)
        self.assertEqual(result['candidate_localization']['tp'],1)
        self.assertIsNone(result['semantic'])
        result=score_batch(obj,self.cases,self.gold,review=self.review(obj,False),dataset_hash='fixture-dataset-hash')
        self.assertEqual(result['semantic']['tp'],0)
        self.assertEqual(result['semantic']['fp'],1)
        self.assertEqual(result['semantic']['fn'],20)

    def test_human_attestation_fixture_path(self):
        obj,_=self.positive_bundle()
        result=score_batch(obj,self.cases,self.gold,review=self.review(obj),dataset_hash='fixture-dataset-hash')
        self.assertEqual(result['semantic']['tp'],1)

    def test_duplicate_identity_rejected_across_types(self):
        obj,row=self.positive_bundle()
        f=copy.deepcopy(row['findings'][0]);f['type']='quantity'
        row['findings'].append(f)
        with self.assertRaisesRegex(ValueError,'duplicate finding'):
            validate_predictions(obj,self.cases)

    def test_shotgun_citations_do_not_match(self):
        obj,row=self.positive_bundle()
        pm=pointer_map(self.cases[self.positive])
        row['findings'][0]['authorized_evidence']=[{'pointer':p,'quote':text} for p,(kind,text) in pm.items() if kind!='draft_proposal']
        self.assertEqual(score_batch(obj,self.cases,self.gold)['candidate_localization']['tp'],0)

    def test_missing_rejected_or_explicitly_penalized(self):
        obj=self.bundle();obj['predictions']=[]
        with self.assertRaisesRegex(ValueError,'missing'):
            score_batch(obj,self.cases,self.gold)
        result=score_batch(obj,self.cases,self.gold,allow_missing=True)
        self.assertEqual(len(result['missing_cases']),30)
        self.assertEqual(result['candidate_localization']['fn'],20)
        self.assertEqual(result['explicit_correct_clearances'],0)

    def test_no_issue_is_separate_from_abstention(self):
        obj=self.bundle()
        for r in obj['predictions']:r['status']='no_issue'
        result=score_batch(obj,self.cases,self.gold)
        self.assertEqual(result['explicit_correct_clearances'],10)
        self.assertEqual(result['candidate_localization']['fn'],20)

    def test_clarification_type_and_action(self):
        cid=next(c for c,g in self.gold.items() if g['category']=='uncertainty')
        cases={cid:self.cases[cid]};gold={cid:self.gold[cid]}
        obj=self.bundle(cases);obj['predictions'][0].update(status='issues',findings=[self.finding(cid)])
        self.assertEqual(score_batch(obj,cases,gold)['candidate_localization']['tp'],1)
        obj['predictions'][0]['findings'][0]['action']='revise_proposal'
        with self.assertRaisesRegex(ValueError,'type/action'):
            score_batch(obj,cases,gold)

    def test_omission_partial_proposal_not_credited(self):
        cid=next(c for c,g in self.gold.items() if g['category']=='omission')
        cases={cid:self.cases[cid]};gold={cid:self.gold[cid]}
        obj=self.bundle(cases);f=self.finding(cid)
        obj['predictions'][0].update(status='issues',findings=[f])
        self.assertEqual(score_batch(obj,cases,gold)['candidate_localization']['tp'],1)
        f['proposal_evidence'].pop()
        self.assertEqual(score_batch(obj,cases,gold)['candidate_localization']['tp'],0)

    def test_two_same_type_issues_not_confused(self):
        # In-memory multi-issue challenge tests the algorithm beyond this single-issue dataset.
        cid=self.positive;cases={cid:copy.deepcopy(self.cases[cid])};gold={cid:copy.deepcopy(self.gold[cid])}
        issue=copy.deepcopy(gold[cid]['issues'][0]);issue['issue_id']=cid+'-02'
        pm=pointer_map(cases[cid])
        alt=next(p for p,(k,_) in pm.items() if k!='draft_proposal' and p not in issue['identity']['authorized_evidence'])
        issue['identity']['authorized_evidence']=[alt];gold[cid]['issues'].append(issue)
        obj=self.bundle(cases);obj['predictions'][0].update(status='issues',findings=[self.finding(cid)])
        result=score_batch(obj,cases,gold)
        self.assertEqual(result['candidate_localization']['tp'],1)
        self.assertEqual(result['candidate_localization']['fn'],1)

    def test_adversarial_malformed_predictions(self):
        good,row=self.positive_bundle();ix=good['predictions'].index(row)
        def field(path,value):
            obj=copy.deepcopy(good);parent=obj
            for k in path[:-1]:parent=parent[k]
            parent[path[-1]]=value
            return obj
        paths=[(['predictions'],None),(['predictions'],{}),(['predictions',ix],None),
               (['predictions',ix,'case_id'],[]),(['predictions',ix,'case_id'],'../gold/E101'),
               (['predictions',ix,'status'],True),(['predictions',ix,'reason'],''),
               (['predictions',ix,'findings'],{}),(['predictions',ix,'findings',0],None),
               (['predictions',ix,'findings',0,'type'],[]),(['predictions',ix,'findings',0,'type'],'no_issue'),
               (['predictions',ix,'findings',0,'claim'],42),(['predictions',ix,'findings',0,'action'],'execute'),
               (['predictions',ix,'findings',0,'authorized_evidence'],[]),
               (['predictions',ix,'findings',0,'authorized_evidence'],[None]),
               (['predictions',ix,'findings',0,'authorized_evidence',0,'pointer'],'d999.p1'),
               (['predictions',ix,'findings',0,'authorized_evidence',0,'quote'],'fabricated quotation'),
               (['input_sha256'],'0'*64),(['dataset_version'],'future')]
        for path,value in paths:
            with self.subTest(path=path,value=value),self.assertRaises(ValueError):
                validate_predictions(field(path,value),self.cases)
        for bad in [None,[],True,'text',42]:
            with self.subTest(root=bad),self.assertRaises(ValueError):validate_predictions(bad,self.cases)

    def test_unknown_fields_rejected_at_every_level(self):
        for level in ['root','row','finding','evidence']:
            obj,row=self.positive_bundle()
            target={'root':obj,'row':row,'finding':row['findings'][0],
                    'evidence':row['findings'][0]['authorized_evidence'][0]}[level]
            target['gold']='sneaked field'
            with self.subTest(level=level),self.assertRaises(ValueError):validate_predictions(obj,self.cases)

    def test_duplicate_records_pointers_wrong_roles(self):
        obj,row=self.positive_bundle();obj['predictions'].append(copy.deepcopy(row))
        with self.assertRaises(ValueError):validate_predictions(obj,self.cases)
        obj,row=self.positive_bundle();f=row['findings'][0]
        f['authorized_evidence']*=2
        with self.assertRaises(ValueError):validate_predictions(obj,self.cases)
        obj,row=self.positive_bundle();f=row['findings'][0]
        f['authorized_evidence']=copy.deepcopy(f['proposal_evidence'])
        with self.assertRaisesRegex(ValueError,'role'):validate_predictions(obj,self.cases)

    def test_status_and_findings_consistent(self):
        obj,row=self.positive_bundle();row['status']='no_issue'
        with self.assertRaises(ValueError):validate_predictions(obj,self.cases)
        obj=self.bundle();obj['predictions'][0]['status']='issues'
        with self.assertRaises(ValueError):validate_predictions(obj,self.cases)

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        for text in ['{"predictions":[],"predictions":[]}','{"a":{"b":1,"b":2}}','NaN','Infinity','-Infinity']:
            with self.subTest(text=text),self.assertRaises(ValueError):loads(text)

    def test_semantic_review_binding_and_completeness(self):
        obj,_=self.positive_bundle()
        for key,value in [('prediction_sha256','bad'),('dataset_sha256','bad'),('qualified_human',False),
                          ('independent',False),('reviewer_id',''),('decisions',[])]:
            rev=self.review(obj);rev[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                score_batch(obj,self.cases,self.gold,review=rev,dataset_hash='fixture-dataset-hash')
        rev=self.review(obj);rev['decisions']*=2
        with self.assertRaises(ValueError):score_batch(obj,self.cases,self.gold,review=rev,dataset_hash='fixture-dataset-hash')

    def test_serializer_allowlist_at_every_nesting_level(self):
        c=copy.deepcopy(self.cases[self.positive]);c['gold']='DO_NOT_EXPORT'
        c['documents'][0]['rationale']='DO_NOT_EXPORT'
        c['documents'][0]['paragraphs'][0]['expected_action']='DO_NOT_EXPORT'
        c['source_context'][0]['category']='DO_NOT_EXPORT'
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(serialize_case(c)))

    def test_exporter_never_reads_gold(self):
        original=read;seen=[]
        def guarded(path):
            seen.append(str(path));self.assertNotIn('gold',Path(path).parts)
            return original(path)
        with patch('exp002.read',side_effect=guarded):
            self.assertEqual(len(load_inputs('development')),18)
            self.assertEqual(len(load_inputs('held_out')),12)
        self.assertFalse(any('/gold/' in p for p in seen))

    def test_input_hash_changes_on_record_mutation(self):
        c=copy.deepcopy(self.cases);c[self.positive]['documents'][0]['paragraphs'][0]['text']+=' altered'
        with self.assertRaisesRegex(ValueError,'input hash'):validate_predictions(self.bundle(),c)

    def test_near_duplicate_detector_catches_copies_and_paragraphs(self):
        cases=copy.deepcopy(self.cases);ids=list(cases)
        cases[ids[1]]['documents']=copy.deepcopy(cases[ids[0]]['documents'])
        report=leakage_report(cases,self.index['cases'])
        self.assertTrue(report['flagged_pairs']);self.assertTrue(report['copied_paragraphs'])

    def test_source_and_family_overlap_detected(self):
        rows=copy.deepcopy(self.index['cases'])
        a=next(r for r in rows if r['split']=='development');b=next(r for r in rows if r['split']=='held_out')
        b['family']=a['family'];b['source_group']=a['source_group']
        report=leakage_report(self.cases,rows)
        self.assertTrue(report['cross_split_overlap']['family'])
        self.assertTrue(report['cross_split_overlap']['source_group'])

    def test_source_cache_missing_not_silently_successful(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaisesRegex(ValueError,'source cache mismatch'):
            verify_source_cache(Path(d))

    def test_fixture_mutations_rejected(self):
        mutations = ['wrong_date', 'fake_page', 'unmarked_synthetic', 'gold_anchor', 'extra_case', 'shared_source_bytes']
        for change in mutations:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp)/'exp002';shutil.copytree(DATA,base)
                path=base/'cases'/f'{self.positive}.json';case=read(path)
                if change=='wrong_date': case['documents'][0]['timestamp']='2026-02-30'
                if change=='fake_page': case['source_context'][0]['pdf_page']=999
                if change=='unmarked_synthetic': case['documents'][0]['synthetic']=False
                path.write_text(json.dumps(case))
                if change=='gold_anchor':
                    path=base/'gold'/f'{self.positive}.json';obj=read(path)
                    obj['issues'][0]['identity']['authorized_evidence']=['d999.p1']
                    path.write_text(json.dumps(obj))
                if change=='extra_case': (base/'cases/E999.json').write_text('{}')
                if change=='shared_source_bytes':
                    path=base/'sources/manifest.json';obj=read(path)
                    dev=next(s for s in obj['sources'] if s.get('partition')=='development')
                    held=next(s for s in obj['sources'] if s.get('partition')=='held_out')
                    held['artifacts'][0]['sha256']=dev['artifacts'][0]['sha256']
                    path.write_text(json.dumps(obj))
                with self.assertRaises(ValueError): validate(base)

    def test_inventory_detects_modified_and_added_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            shutil.copytree(DATA,root/'data/exp002')
            shutil.copytree(ROOT/'prompts/exp002',root/'prompts/exp002')
            baseline=inventory(root)
            p=root/'data/exp002/cases'/f'{self.positive}.json'
            p.write_text(p.read_text()+'\n')
            self.assertNotEqual(inventory(root),baseline)
            (root/'data/exp002/unexpected.json').write_text('{}')
            self.assertIn('data/exp002/unexpected.json',inventory(root))
            with self.assertRaisesRegex(ValueError,'inventory/hash mismatch'): verify_integrity(root)

    def test_blinded_packet_is_exact_allowlisted_inputs_and_pending(self):
        packet=read(DATA/'review/sample_inputs.json');status=read(DATA/'review/audit_status.json')
        self.assertEqual(len(packet['inputs']),6)
        self.assertEqual({self.gold[c['case_id']]['category'] for c in packet['inputs']},
                         {'contradiction','omission','supersession','quantity','uncertainty','clean'})
        for case in packet['inputs']:
            self.assertEqual(case,serialize_case(self.cases[case['case_id']]))
        self.assertEqual(status['sample_input_sha256'],hashlib.sha256(canonical(packet['inputs'])).hexdigest())
        self.assertEqual(status['completed_case_reviews'],0)
        self.assertEqual(status['status'],'pending')

    def test_cli_rejects_malformed_batch_without_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.json';path.write_text('{"predictions": [], "predictions": []}')
            result=subprocess.run([sys.executable,str(ROOT/'scripts/score_exp002.py'),
                                   '--split','held_out','--predictions',str(path)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('duplicate JSON key',result.stderr)
            self.assertEqual(result.stdout,'')

    def test_all_identity_fixtures_are_candidates_not_model_results(self):
        obj=self.bundle()
        for row in obj['predictions']:
            cid=row['case_id']
            row['status']=self.gold[cid]['expected_status']
            row['findings']=[self.finding(cid)] if self.gold[cid]['issues'] else []
        result=score_batch(obj,self.cases,self.gold)
        self.assertEqual(result['candidate_localization'],{'tp':20,'fp':0,'fn':0,'precision':1.0,'recall':1.0})
        self.assertEqual(result['explicit_correct_clearances'],10)
        self.assertIsNone(result['semantic'])

    def test_legacy_type_only_failure_preserved(self):
        from score import score
        obj=read(ROOT/'examples/empty_predictions.json')
        obj['predictions'][0]['findings']=[{'type':'contradiction','claim':'Wrong item: paint is blue.',
                                           'action':'Ask a reviewer','evidence':['visit','proposal']}]
        self.assertEqual(score(obj)['tp'],1)


if __name__=='__main__':unittest.main()
