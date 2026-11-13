#!/usr/bin/env python3
"""Deterministic, outcome-blind LibriSpeech dev-clean subset selection."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import tarfile

OFFICIAL_MD5 = '42e2234ba48799c1f50f24a7926300a1'


def select(archive,output):
    digest=hashlib.md5()
    with archive.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): digest.update(block)
    if digest.hexdigest()!=OFFICIAL_MD5:
        raise ValueError('Archive does not match the official dev-clean MD5.')
    candidates={}; transcripts={}; speakers={}; licence=None
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            if not member.isfile(): continue
            name=Path(member.name)
            if name.name=='LICENSE.TXT':
                licence=tar.extractfile(member).read().decode()
            elif name.name=='SPEAKERS.TXT':
                for line in tar.extractfile(member).read().decode().splitlines():
                    if not line.strip() or line.startswith(';'): continue
                    fields=[part.strip() for part in line.split('|')]
                    if fields[2]=='dev-clean': speakers[fields[0]]=fields[1]
            elif name.name.endswith('.trans.txt'):
                for line in tar.extractfile(member).read().decode().splitlines():
                    key,text=line.split(' ',1); transcripts[key]=text
            elif name.suffix=='.flac':
                speaker=name.stem.split('-')[0]
                if len(candidates.get(speaker,[]))>=2: continue
                source=tar.extractfile(member); header=source.read(26)
                if header[:4]!=b'fLaC': raise ValueError('Invalid FLAC header')
                packed=int.from_bytes(header[18:26],'big')
                rate=packed>>44; samples=packed & ((1<<36)-1)
                duration=samples/rate
                if 4<=duration<=10:
                    candidates.setdefault(speaker,[]).append((name.stem,header+source.read(),duration))
    if licence is None: raise ValueError('Corpus licence missing')
    chosen=[]
    for sex in ['F','M']:
        eligible=sorted((s for s,label in speakers.items() if label==sex and len(candidates.get(s,[]))==2),key=int)
        if len(eligible)<3: raise ValueError('Insufficient eligible speakers')
        chosen.extend(eligible[:3])
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for speaker in chosen:
        for utterance,data,duration in candidates[speaker]:
            path=output/(utterance+'.flac'); path.write_bytes(data)
            rows.append({'utterance':utterance,'speaker':speaker,'corpus_sex_label':speakers[speaker],
                'duration_seconds':duration,'source_file':path.name,'transcript':transcripts[utterance],
                'sha256':hashlib.sha256(data).hexdigest()})
    with (output/'selection.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (output/'LICENSE.txt').write_text(licence)
    method={'corpus':'LibriSpeech dev-clean','url':'https://www.openslr.org/resources/12/dev-clean.tar.gz',
        'archive_md5':digest.hexdigest(),'selection_rule':'First 3 numerically sorted eligible speaker IDs per corpus F/M label; first 2 files in archive order of duration 4–10 s per speaker. No codec outcome used.',
        'utterances':len(rows),'speakers':chosen,'total_seconds':sum(r['duration_seconds'] for r in rows)}
    (output/'selection.json').write_text(json.dumps(method,indent=2)+'\n')
    print(json.dumps(method,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path); parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(); select(args.archive,args.output)
