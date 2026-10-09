#!/usr/bin/env python3
"""Export ONLY allowlisted model inputs; does not open answer-key files."""
import argparse
import hashlib
import json
from exp002 import canonical, load_inputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split',choices=['development','held_out'],required=True)
    args=parser.parse_args()
    cases=load_inputs(args.split)
    print(json.dumps({'input_sha256':hashlib.sha256(canonical(cases)).hexdigest(),
                      'inputs':cases},ensure_ascii=False,indent=2))


if __name__=='__main__': main()
