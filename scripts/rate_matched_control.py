#!/usr/bin/env python3
"""Secondary control: choose Opus bitrate using file size only, not quality."""
import argparse
import csv
import json
from pathlib import Path
import tempfile
import numpy as np
from pystoi import stoi
import prepare_codecs as codec
import analyse_corpus as analysis


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('corpus',type=Path);parser.add_argument('analysis',type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    baseline=list(csv.DictReader((args.analysis/'all_conditions.csv').open()))
    args.output.mkdir(parents=True,exist_ok=False);results=[]
    for path in sorted(args.corpus.glob('*/manifest.json')):
        manifest=json.loads(path.read_text());base=path.parent;x=analysis.read_wav(base/manifest['original'])
        output=args.output/manifest['utterance'];output.mkdir();duration=len(x)/24000
        X=[analysis.stft(x,c)[0] for c in analysis.CONFIGS]
        for bandwidth in [6,12]:
            neural=next(c for c in manifest['conditions'] if c['codec']=='encodec' and c['nominal_kbps']==bandwidth)
            original_opus=next(c for c in manifest['conditions'] if c['codec']=='opus' and c['nominal_kbps']==bandwidth)
            target=neural['measured_kbps']
            guess=round((bandwidth-original_opus['measured_kbps']+target)*1000/400)*400
            trials=[]
            with tempfile.TemporaryDirectory(dir=output) as temp:
                for requested in [guess-400,guess,guess+400]:
                    encoded=Path(temp)/f'{requested}.opus'
                    enc,_=codec.opus_commands(base/manifest['original'],encoded,Path(temp)/'unused.wav',requested/1000)
                    codec.command(enc)
                    measured=encoded.stat().st_size*8/duration/1000
                    trials.append({'requested_bps':requested,'measured_kbps':measured})
            chosen=min(trials,key=lambda r:abs(r['measured_kbps']-target))['requested_bps']
            encoded=output/f'opus_matched_{bandwidth}k.opus';decoded=output/f'opus_matched_{bandwidth}k.wav'
            enc,dec=codec.opus_commands(base/manifest['original'],encoded,decoded,chosen/1000)
            enc_s=codec.timed(enc);dec_s=codec.timed(dec);y=analysis.read_wav(decoded)
            if len(y)!=len(x):raise ValueError('Matched control changed length')
            nmse,sdr=analysis.waveform_metrics(x,y);measured=encoded.stat().st_size*8/duration/1000
            row={'utterance':manifest['utterance'],'speaker':manifest['corpus']['speaker'],
                'comparison_bandwidth_kbps':bandwidth,'opus_requested_kbps':chosen/1000,
                'opus_measured_kbps':measured,'encodec_measured_kbps':target,
                'relative_pair_rate_gap':abs(measured-target)/((measured+target)/2),
                'opus_nmse':nmse,'opus_si_sdr_db':sdr,'opus_stoi':float(stoi(x,y,24000,extended=False)),
                'opus_encode_seconds':enc_s,'opus_decode_seconds':dec_s}
            scores=[]
            for c,reference in zip(analysis.CONFIGS,X):
                log_db,_,score=analysis.spectral_error(reference,analysis.stft(y,c)[0])
                row['opus_'+c[0]+'_log_db']=log_db;scores.append(score)
            row['opus_mr_error']=float(np.mean(scores))
            peer=next(r for r in baseline if r['utterance']==manifest['utterance'] and r['codec']=='encodec' and int(r['nominal_kbps'])==bandwidth)
            for metric in ['nmse','si_sdr_db','stoi','short_log_db','medium_log_db','long_log_db','mr_error']:
                row['encodec_'+metric]=float(peer[metric])
            results.append(row)
            (output/f'control_{bandwidth}k.json').write_text(json.dumps({'selection_rule':'Nearest measured total file bitrate among three adjacent 400-bps CBR settings; no quality metric used.',
                'trials':trials,'chosen_requested_bps':chosen,'encoded_sha256':codec.sha256(encoded),
                'decoded_sha256':codec.sha256(decoded),'result':row},indent=2)+'\n')
        print('Rate-matched control',manifest['utterance'],flush=True)
    analysis.write_csv(args.output/'all_conditions.csv',results)
    summary=[]
    for bandwidth in [6,12]:
        rs=[r for r in results if r['comparison_bandwidth_kbps']==bandwidth]
        record={'comparison_bandwidth_kbps':bandwidth,'utterances':len(rs),
                'mean_relative_pair_rate_gap':float(np.mean([r['relative_pair_rate_gap'] for r in rs]))}
        for name in ['opus','encodec']:
            for metric in ['measured_kbps','nmse','si_sdr_db','stoi','short_log_db','medium_log_db','long_log_db','mr_error']:
                record[name+'_'+metric+'_mean']=float(np.mean([r[name+'_'+metric] for r in rs]))
        summary.append(record)
    analysis.write_csv(args.output/'summary.csv',summary)
    if len(results)!=24:raise ValueError('Expected 24 matched-rate Opus controls')


if __name__=='__main__':main()
