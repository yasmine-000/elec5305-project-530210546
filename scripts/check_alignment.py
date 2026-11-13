#!/usr/bin/env python3
"""Report global-lag sensitivity without changing primary audio/metrics."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy import signal
import analyse_corpus as analysis


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('corpus',type=Path)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    rows=[]
    for path in sorted(args.corpus.glob('*/manifest.json')):
        manifest=json.loads(path.read_text());x=analysis.read_wav(path.parent/manifest['original']);xc=x-x.mean()
        for entry in manifest['conditions']:
            y=analysis.read_wav(path.parent/entry['decoded']);yc=y-y.mean()
            correlation=signal.correlate(yc,xc,mode='full',method='fft');centre=len(x)-1
            lag=int(np.argmax(correlation[centre-1200:centre+1201])-1200) # ±50 ms
            xx=x[:-lag] if lag>0 else (x[-lag:] if lag<0 else x)
            yy=y[lag:] if lag>0 else (y[:lag] if lag<0 else y)
            rows.append({'utterance':manifest['utterance'],'codec':entry['codec'],
                'nominal_kbps':entry['nominal_kbps'],'best_global_lag_samples':lag,
                'unaligned_si_sdr_db':analysis.waveform_metrics(x,y)[1],
                'global_lag_sensitivity_si_sdr_db':analysis.waveform_metrics(xx,yy)[1]})
    if len(rows)!=48:raise ValueError('Expected 48 primary cases')
    analysis.write_csv(args.output,rows)
    print('Global alignment sensitivity recorded; original WAVs and primary scores were not altered.')


if __name__=='__main__':main()
