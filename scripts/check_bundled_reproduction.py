#!/usr/bin/env python3
"""Recompute published metrics using ONLY a fresh extraction of the release ZIP."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile
import numpy as np
from pystoi import stoi
import analyse_corpus as analysis


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--octave',type=Path)
    args=parser.parse_args();repo=args.repo.resolve()
    archive=repo/'deliverables/matlab_online_data.zip'
    expected=json.loads((repo/'experiments/real_speech/evidence_manifest.json').read_text())
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected['data_zip_sha256']
    published=list(csv.DictReader((repo/'experiments/real_speech/all_conditions.csv').open()))
    lookup={(r['utterance'],r['codec'],int(r['nominal_kbps'])):r for r in published}
    discrepancies={};conditions=0
    with tempfile.TemporaryDirectory(prefix='codecdiag-fresh-') as directory:
        fresh=Path(directory)
        with zipfile.ZipFile(archive) as bundle:
            for name in bundle.namelist():
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert bundle.testzip() is None
            bundle.extractall(fresh)
        corpus=fresh/'experiment_data/real_codecs'
        manifests=sorted(corpus.glob('*/manifest.json'));assert len(manifests)==12
        for path in manifests:
            m=json.loads(path.read_text());base=path.parent
            analysis.assert_hash(base/m['original'],m['prepared_sha256']);x=analysis.read_wav(base/m['original'])
            X=[analysis.stft(x,c)[0] for c in analysis.CONFIGS]
            assert len(m['conditions'])==4
            for entry in m['conditions']:
                analysis.assert_hash(base/entry['decoded'],entry['decoded_sha256'])
                analysis.assert_hash(base/entry['encoded'],entry['encoded_sha256'])
                y=analysis.read_wav(base/entry['decoded']);assert len(y)==len(x)
                reference=lookup[(m['utterance'],entry['codec'],int(entry['nominal_kbps']))]
                nmse,sdr=analysis.waveform_metrics(x,y)
                values={'nmse':nmse,'si_sdr_db':sdr,'stoi':float(stoi(x,y,24000,extended=False)),
                    'measured_kbps':(base/entry['encoded']).stat().st_size*8/(len(x)/24000)/1000}
                scores=[]
                for c,spectrum in zip(analysis.CONFIGS,X):
                    log_db,convergence,score=analysis.spectral_error(spectrum,analysis.stft(y,c)[0])
                    values[c[0]+'_log_db']=log_db;values[c[0]+'_convergence']=convergence
                    values[c[0]+'_normalised']=score;scores.append(score)
                values['mr_error']=float(np.mean(scores))
                for metric,value in values.items():
                    difference=abs(value-float(reference[metric]));assert difference<1e-9,(metric,difference)
                    discrepancies[metric]=max(discrepancies.get(metric,0),difference)
                conditions+=1
        octave_log=None
        if args.octave:
            quote=lambda value:str(value).replace("'","''")
            core_output=fresh/'octave_fresh.csv'
            expression=(f"addpath('{quote(repo)}'); addpath('{quote(repo/'tests')}'); "
                f"run_octave_core_tests('{quote(core_output)}','{quote(corpus)}');")
            result=subprocess.run([str(args.octave),'--quiet','--no-history','--eval',expression],
                                  capture_output=True,text=True,check=True)
            octave_log=result.stdout
            core=list(csv.DictReader(core_output.open()));assert len(core)==60
            assert max(float(r['max_absolute_error']) for r in core)<1e-10
        assert conditions==48
    report={'data_zip_sha256':expected['data_zip_sha256'],'fresh_extraction_only':True,
        'primary_conditions_recomputed':conditions,'metrics_per_condition':len(discrepancies),
        'numeric_comparisons':conditions*len(discrepancies),'absolute_tolerance':1e-9,
        'maximum_absolute_discrepancy':discrepancies,'octave_stdout':octave_log,
        'native_matlab_executed':False,'passed':True}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
