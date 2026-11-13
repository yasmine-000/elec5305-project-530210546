#!/usr/bin/env python3
"""Separate original 0–8-kHz information from resampled 8–12-kHz energy."""
import argparse
import json
from pathlib import Path
import numpy as np
import analyse_corpus as analysis


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('corpus',type=Path)
    parser.add_argument('--matched',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False);rows=[]
    for path in sorted(args.corpus.glob('*/manifest.json')):
        manifest=json.loads(path.read_text());base=path.parent;x=analysis.read_wav(base/manifest['original'])
        spectra=[analysis.stft(x,c)[0] for c in analysis.CONFIGS]
        conditions=[('primary',e['codec'],e['nominal_kbps'],base/e['decoded']) for e in manifest['conditions']]
        for bitrate in [6,12]:
            conditions.append(('matched_rate','opus',bitrate,args.matched/manifest['utterance']/f'opus_matched_{bitrate}k.wav'))
        for design,codec,bandwidth,decoded in conditions:
            y=analysis.read_wav(decoded);scores=[]
            row={'utterance':manifest['utterance'],'speaker':manifest['corpus']['speaker'],
                 'design':design,'codec':codec,'comparison_bandwidth_kbps':bandwidth}
            for c,X in zip(analysis.CONFIGS,spectra):
                Y=analysis.stft(y,c)[0];frequency=np.abs(np.fft.fftfreq(c[3],1/24000))
                bins=frequency<=8000
                error,conv,score=analysis.spectral_error(X[bins],Y[bins]);scores.append(score)
                row[c[0]+'_inband_log_db']=error;row[c[0]+'_inband_convergence']=conv
                if c[0]=='medium':
                    reference_power=np.abs(X)**2;decoded_power=np.abs(Y)**2
                    row['reference_above8k_power_fraction']=float(reference_power[~bins].sum()/reference_power.sum())
                    row['decoded_above8k_power_fraction']=float(decoded_power[~bins].sum()/decoded_power.sum())
                    high=(frequency>=4000)&(frequency<=8000)
                    row['decoded_4_to_8k_energy_ratio_db']=float(10*np.log10(max(decoded_power[high].sum(),1e-20)/max(reference_power[high].sum(),1e-20)))
            row['inband_mr_error']=float(np.mean(scores));rows.append(row)
    if len(rows)!=72:raise ValueError('Expected 48 primary +24 matched-rate control rows')
    analysis.write_csv(args.output/'all_conditions.csv',rows)
    summary=[]
    for design in ['primary','matched_rate']:
        for codec in ['opus','encodec']:
            if design=='matched_rate' and codec=='encodec':continue
            for bitrate in [6,12]:
                subset=[r for r in rows if r['design']==design and r['codec']==codec and r['comparison_bandwidth_kbps']==bitrate]
                row={'design':design,'codec':codec,'comparison_bandwidth_kbps':bitrate,'utterances':len(subset)}
                for metric in ['short_inband_log_db','medium_inband_log_db','long_inband_log_db','inband_mr_error',
                               'reference_above8k_power_fraction','decoded_above8k_power_fraction','decoded_4_to_8k_energy_ratio_db']:
                    row[metric+'_mean']=float(np.mean([r[metric] for r in subset]))
                summary.append(row)
    analysis.write_csv(args.output/'summary.csv',summary)
    print('Completed 72 in-band sensitivity cases; above-8-kHz energy is not original speech.',flush=True)


if __name__=='__main__':main()
