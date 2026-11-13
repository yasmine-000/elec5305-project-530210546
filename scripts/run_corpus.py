#!/usr/bin/env python3
"""Run serial same-machine paired codec preparation over selection.csv."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('selection',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    rows=list(csv.DictReader(args.selection.open()))
    args.output.mkdir(parents=True,exist_ok=False)
    completed=[]
    for index,row in enumerate(rows,1):
        source=(args.selection.parent/row['source_file']).resolve()
        if hashlib.sha256(source.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Selected source hash changed')
        destination=(args.output/row['utterance']).resolve()
        cmd=[sys.executable,Path(__file__).with_name('prepare_codecs.py').resolve(),source,
             '--output',destination,'--codecs','opus','encodec','--bitrates','6','12']
        print(f'[{index}/{len(rows)}] {row["utterance"]} ({row["duration_seconds"]} s)',flush=True)
        start=time.perf_counter()
        run=subprocess.run(list(map(str,cmd)),capture_output=True,text=True)
        (args.output/(row['utterance']+'.log')).write_text(run.stdout+'\n'+run.stderr)
        print(run.stdout,flush=True)
        if run.returncode:
            raise RuntimeError(f'Codec preparation failed; inspect {row["utterance"]}.log')
        manifest=json.loads((destination/'manifest.json').read_text())
        if len(manifest['conditions'])!=4: raise ValueError('Incomplete paired conditions')
        manifest['corpus']=dict(row)
        (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        completed.append({'utterance':row['utterance'],'wall_seconds':time.perf_counter()-start})
        (args.output/'completed.json').write_text(json.dumps(completed,indent=2)+'\n')
    print(f'Completed {len(completed)} utterances, {4*len(completed)} real codec conditions.',flush=True)


if __name__=='__main__': main()
