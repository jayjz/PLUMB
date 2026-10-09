#!/usr/bin/env python3
"""CI-safe, offline checks. Source-cache byte verification is an explicit local check."""
import argparse
import json
from collections import Counter
from pathlib import Path
from exp002 import validate, verify_integrity, verify_source_cache


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-cache',type=Path)
    args=parser.parse_args()
    try:
        cases,gold,index,leakage=validate()
        result={'status':'PASS','cases':len(cases),'issues':sum(len(g['issues']) for g in gold.values()),
                'categories':dict(sorted(Counter(r['category'] for r in index['cases']).items())),
                'splits':dict(sorted(Counter(r['split'] for r in index['cases']).items())),
                'dataset_sha256':verify_integrity(),'leakage':leakage,
                'source_cache_artifacts_checked':verify_source_cache(args.source_cache) if args.source_cache else None,
                'source_cache_note':'Original downloads are local only. CI checks provenance metadata and frozen factual notes, not unavailable PDF bytes.',
                'independent_human_review':False,'model_run':False}
    except (ValueError,KeyError,TypeError,OSError) as err:
        parser.error(str(err))
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
