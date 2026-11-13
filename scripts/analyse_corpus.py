#!/usr/bin/env python3
"""Actual Python/SciPy analysis; never described as a MATLAB execution."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/codecdiag-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.io import wavfile
from pystoi import stoi

RATE=24000
CONFIGS=[('short',288,72,512),('medium',672,168,1024),('long',1344,336,2048)]


def read_wav(path):
    rate,x=wavfile.read(path)
    if rate!=RATE or x.ndim!=1 or not np.all(np.isfinite(x)):
        raise ValueError(f'Invalid mono reference/output: {path}')
    if np.issubdtype(x.dtype,np.integer):
        x=x.astype(float)/max(abs(np.iinfo(x.dtype).min),np.iinfo(x.dtype).max)
    return x.astype(np.float64)


def stft(x,config):
    _,length,hop,nfft=config
    window=signal.windows.hann(length,sym=False)
    padded=np.pad(x,(length,length))
    frames=1+math.ceil((len(padded)-length)/hop)
    padded=np.pad(padded,(0,(frames-1)*hop+length-len(padded)))
    segments=np.lib.stride_tricks.sliding_window_view(padded,length)[::hop]
    spectrum=np.fft.fft(segments*window,n=nfft,axis=1).T
    times=(np.arange(frames)*hop+length/2-length)/RATE
    keep=(times>=0)&(times<len(x)/RATE)
    return spectrum[:,keep],times[keep]


def spectral_error(reference,decoded):
    a=np.abs(reference); b=np.abs(decoded)
    floor=max(a.max()*1e-5,np.finfo(float).eps)
    log_db=np.mean(np.abs(20*np.log10(np.maximum(b,floor))-20*np.log10(np.maximum(a,floor))))
    convergence=np.linalg.norm(b-a)/max(np.linalg.norm(a),np.finfo(float).eps)
    return float(log_db),float(convergence),float(0.5*(log_db/100+convergence))


def waveform_metrics(x,y):
    nmse=np.sum((y-x)**2)/np.sum(x*x)
    a=x-x.mean(); b=y-y.mean()
    target=np.dot(a,b)/np.dot(a,a)*a
    target_power=np.sum(target*target); error_power=np.sum((b-target)**2)
    sdr=10*np.log10(target_power/error_power) if error_power else float('inf')
    return float(nmse),float(sdr)


def assert_hash(path,expected):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise ValueError(f'Hash mismatch: {path}')


def select_regions(x):
    """Reference-only acoustic proxies, not ground-truth phonetic labels."""
    length=600; hop=240
    frames=np.lib.stride_tricks.sliding_window_view(x,length)[::hop]
    energy=np.mean(frames**2,axis=1)
    window=signal.windows.hann(length,sym=False)
    spectrum=np.fft.rfft(frames*window,n=1024,axis=1)
    power=np.abs(spectrum)**2
    frequencies=np.fft.rfftfreq(1024,1/RATE)
    hf=np.sum(power[:,(frequencies>=4000)&(frequencies<=8000)],axis=1)/np.maximum(power.sum(axis=1),1e-20)
    centred=frames-frames.mean(axis=1,keepdims=True)
    fft=np.fft.rfft(centred,n=2048,axis=1)
    ac=np.fft.irfft(np.abs(fft)**2,n=2048,axis=1)
    cumulative=np.c_[np.zeros(len(frames)),np.cumsum(centred**2,axis=1)]
    periodicity=np.zeros(len(frames))
    for lag in range(60,301):
        denominator=np.sqrt(cumulative[:,length-lag]*(cumulative[:,length]-cumulative[:,lag]))
        periodicity=np.maximum(periodicity,ac[:,lag]/np.maximum(denominator,1e-20))
    gate=energy>energy.max()*0.04
    # Smooth over 200 ms to prefer a stable interval rather than one noisy frame.
    kernel=np.ones(20)/20
    voiced=np.convolve(np.where(gate,periodicity,0),kernel,mode='same')
    fricative=np.convolve(np.where(gate & (periodicity<0.5),hf,0),kernel,mode='same')
    magnitude=np.sqrt(power)
    flux=np.r_[0,np.sum(np.maximum(np.diff(magnitude,axis=0),0)**2,axis=1)]
    flux=np.where(gate,flux,0)
    times=(np.arange(len(frames))*hop+length/2)/RATE
    regions=[]
    for kind,values,threshold,before,after in [
        ('harmonic',voiced,0.55,0.12,0.12),
        ('transient',flux,1e-12,0.025,0.075),
        ('fricative',fricative,0.035,0.10,0.10)]:
        candidates=values.copy()
        candidates[(times<before+0.02)|(times>len(x)/RATE-after-0.02)]=0
        index=int(np.argmax(candidates))
        if candidates[index]<threshold: continue
        regions.append({'type':kind,'start_seconds':float(times[index]-before),
                        'end_seconds':float(times[index]+after),'selection_score':float(candidates[index]),
                        'annotation_method':'automatic reference-only acoustic proxy, not phonetic ground truth'})
    return regions


def regional_metrics(x,y,regions):
    rows=[]
    for region in regions:
        a=int(np.floor(region['start_seconds']*RATE)); b=int(np.ceil(region['end_seconds']*RATE))
        xr=x[a:b]; yr=y[a:b]
        short=spectral_error(stft(xr,CONFIGS[0])[0],stft(yr,CONFIGS[0])[0])[0]
        long=spectral_error(stft(xr,CONFIGS[2])[0],stft(yr,CONFIGS[2])[0])[0]
        nmse,_=waveform_metrics(xr,yr)
        rows.append({**region,'nmse':nmse,'short_log_db':short,'long_log_db':long,
            'peak_time_difference_ms':(np.argmax(np.abs(yr))-np.argmax(np.abs(xr)))/RATE*1000,
            'energy_ratio_db':float(10*np.log10(max(np.sum(yr*yr),1e-20)/max(np.sum(xr*xr),1e-20)))})
    return rows


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)


def condition_plots(x,y,reference_spectra,output,stem,regions):
    figure,axes=plt.subplots(4,3,figsize=(14,11),layout='constrained')
    for column,config in enumerate(CONFIGS):
        X,times=reference_spectra[column]; Y,_=stft(y,config)
        bins=config[3]//2+1; A=np.abs(X[:bins]); B=np.abs(Y[:bins])
        scale=max(A.max(),1e-20); floor=scale*1e-5
        panels=[20*np.log10(np.maximum(A,floor)/scale),20*np.log10(np.maximum(B,floor)/scale),
                20*np.log10(np.maximum(np.abs(Y[:bins]-X[:bins]),floor)/scale),
                20*np.log10(np.maximum(B,floor)/np.maximum(A,floor))]
        for row,(panel,title) in enumerate(zip(panels,['Original','Decoded','Complex error STFT','Signed magnitude difference'])):
            ax=axes[row,column]; limits=(-40,40) if row==3 else (-100,0)
            image=ax.imshow(panel,origin='lower',aspect='auto',extent=[times[0],times[-1],0,12],
                            vmin=limits[0],vmax=limits[1],cmap='coolwarm' if row==3 else 'magma')
            ax.set(title=f'{title}: {config[0]} ({config[1]/RATE*1000:g} ms)',xlabel='Time (s)',ylabel='Frequency (kHz)')
            ax.set_xlim(0,len(x)/RATE)
            figure.colorbar(image,ax=ax,label='dB')
    figure.suptitle(stem+' — actual speech; Python/SciPy analysis')
    figure.savefig(output/(stem+'_spectra.png'),dpi=110);plt.close(figure)
    figure,axes=plt.subplots(2,1,figsize=(12,5),layout='constrained',sharex=True)
    times=np.arange(len(x))/RATE
    axes[0].plot(times,x,lw=.5,label='Original');axes[0].plot(times,y,lw=.5,alpha=.7,label='Decoded')
    axes[0].legend();axes[0].set_ylabel('Amplitude')
    axes[1].plot(times,y-x,lw=.5);axes[1].set(xlabel='Time (s)',ylabel='Decoded − original')
    for region in regions:
        for ax in axes:ax.axvspan(region['start_seconds'],region['end_seconds'],alpha=.12)
    figure.suptitle(stem);figure.savefig(output/(stem+'_waveform.png'),dpi=110);plt.close(figure)


def reference_region_plot(x,regions,path):
    X,times=stft(x,CONFIGS[1]); magnitude=np.abs(X[:513]); scale=magnitude.max()
    figure,axes=plt.subplots(2,1,figsize=(12,5),layout='constrained',sharex=True)
    axes[0].plot(np.arange(len(x))/RATE,x,lw=.4);axes[0].set_ylabel('Amplitude')
    axes[1].imshow(20*np.log10(np.maximum(magnitude,scale*1e-5)/scale),origin='lower',aspect='auto',
                  extent=[times[0],times[-1],0,12],vmin=-80,vmax=0,cmap='magma')
    axes[1].set(xlabel='Time (s)',ylabel='Frequency (kHz)')
    axes[1].set_xlim(0,len(x)/RATE)
    for region in regions:
        for ax in axes:ax.axvspan(region['start_seconds'],region['end_seconds'],alpha=.2,color='cyan')
        axes[0].text(region['start_seconds'],max(x)*.8,region['type']+' proxy',fontsize=8)
    figure.suptitle('Reference-only heuristic regions: not phonetic annotations; source 16 kHz')
    figure.savefig(path,dpi=130);plt.close(figure)


def aggregate(rows,region_rows,output):
    metrics=['measured_kbps','nmse','si_sdr_db','stoi','short_log_db','medium_log_db','long_log_db',
             'mr_error','real_time_factor']
    grouped=[]
    for codec in ['opus','encodec']:
        for bitrate in [6,12]:
            subset=[r for r in rows if r['codec']==codec and r['nominal_kbps']==bitrate]
            result={'codec':codec,'nominal_kbps':bitrate,'utterances':len(subset),
                    'speakers':len(set(r['speaker'] for r in subset))}
            for metric in metrics:
                values=np.array([r[metric] for r in subset]);result[metric+'_mean']=float(values.mean())
                result[metric+'_std']=float(values.std(ddof=1))
            grouped.append(result)
    write_csv(output/'summary.csv',grouped)
    # Paired speaker-cluster bootstrap; exploratory with only six speakers.
    rng=np.random.default_rng(5305);speakers=sorted(set(r['speaker'] for r in rows))
    bootstrap=rng.integers(0,len(speakers),size=(5000,len(speakers)));differences=[];speaker_rows=[]
    for bitrate in [6,12]:
        for metric in metrics[1:]:
            per_speaker=[]
            for speaker in speakers:
                selected={codec:{r['utterance']:r[metric] for r in rows if r['speaker']==speaker and
                          r['nominal_kbps']==bitrate and r['codec']==codec} for codec in ['opus','encodec']}
                if selected['opus'].keys()!=selected['encodec'].keys():raise ValueError('Unpaired speaker data')
                value=np.mean([selected['encodec'][u]-selected['opus'][u] for u in selected['opus']])
                per_speaker.append(value);speaker_rows.append({'speaker':speaker,'nominal_kbps':bitrate,
                    'metric':metric,'encodec_minus_opus':float(value)})
            values=np.array(per_speaker);distribution=values[bootstrap].mean(axis=1)
            lo,hi=np.percentile(distribution,[2.5,97.5])
            differences.append({'nominal_kbps':bitrate,'metric':metric,'encodec_minus_opus':float(values.mean()),
                'speaker_cluster_ci95_low':float(lo),'speaker_cluster_ci95_high':float(hi),'speakers':len(speakers)})
    write_csv(output/'paired_differences.csv',differences);write_csv(output/'speaker_differences.csv',speaker_rows)
    fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
    for ax,scale in zip(axes,['short','medium','long']):
        for codec in ['opus','encodec']:
            rs=[r for r in grouped if r['codec']==codec]
            ax.errorbar([r['measured_kbps_mean'] for r in rs],[r[scale+'_log_db_mean'] for r in rs],
                        [r[scale+'_log_db_std'] for r in rs],fmt='-o',capsize=3,label=codec)
        ax.set(title=scale,xlabel='Measured container bitrate (kb/s)',ylabel='Log magnitude error (dB)');ax.legend();ax.grid(alpha=.3)
    fig.savefig(output/'bitrate_spectral_error.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
    for ax,metric,label in zip(axes,['si_sdr_db','stoi','mr_error'],['SI-SDR (dB; higher better)','STOI (higher better)','MR error (lower better)']):
        for codec in ['opus','encodec']:
            rs=[r for r in grouped if r['codec']==codec]
            ax.plot([r['nominal_kbps'] for r in rs],[r[metric+'_mean'] for r in rs],'-o',label=codec)
        ax.set(xlabel='Target bitrate (kb/s)',ylabel=label);ax.legend();ax.grid(alpha=.3)
    fig.savefig(output/'global_metrics.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4),layout='constrained')
    for codec in ['opus','encodec']:
        rs=[r for r in grouped if r['codec']==codec]
        ax.plot([r['real_time_factor_mean'] for r in rs],[r['mr_error_mean'] for r in rs],'-o',label=codec)
        for r in rs:ax.annotate(str(r['nominal_kbps'])+'k',(r['real_time_factor_mean'],r['mr_error_mean']))
    ax.set(xlabel='End-to-end RTF (includes process/model startup)',ylabel='MR error');ax.legend();ax.grid(alpha=.3)
    fig.savefig(output/'quality_complexity.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4),layout='constrained')
    for codec in ['opus','encodec']:
        for bitrate in [6,12]:
            rs=[r for r in region_rows if r['codec']==codec and r['nominal_kbps']==bitrate]
            a=[r['long_log_db'] for r in rs if r['type']=='harmonic'];b=[r['short_log_db'] for r in rs if r['type']=='transient']
            if a and b:ax.plot(np.mean(a),np.mean(b),'o',label=f'{codec} {bitrate}k')
    ax.set(xlabel='Harmonic-proxy long-window error (dB)',ylabel='Transient-proxy short-window error (dB)');ax.legend();ax.grid(alpha=.3)
    fig.savefig(output/'harmonic_transient.png',dpi=160);plt.close(fig)
    disagreements=[]
    for utterance in sorted(set(r['utterance'] for r in rows)):
        for bitrate in [6,12]:
            pair={r['codec']:r for r in rows if r['utterance']==utterance and r['nominal_kbps']==bitrate}
            mid=np.sign(pair['encodec']['medium_normalised']-pair['opus']['medium_normalised'])
            multi=np.sign(pair['encodec']['mr_error']-pair['opus']['mr_error'])
            short=np.sign(pair['encodec']['short_log_db']-pair['opus']['short_log_db'])
            long=np.sign(pair['encodec']['long_log_db']-pair['opus']['long_log_db'])
            disagreements.append({'utterance':utterance,'nominal_kbps':bitrate,
                'medium_vs_mr_ranking_changes':int(mid!=multi),'short_vs_long_ranking_changes':int(short!=long)})
    write_csv(output/'ranking_disagreements.csv',disagreements)
    return grouped,differences,disagreements


def analyse(root,output):
    output.mkdir(parents=True,exist_ok=False);rows=[];region_rows=[];all_manifests=[]
    for manifest_path in sorted(root.glob('*/manifest.json')):
        manifest=json.loads(manifest_path.read_text());base=manifest_path.parent
        if len(manifest['conditions'])!=4:raise ValueError('Incomplete core experiment')
        assert_hash(base/manifest['original'],manifest['prepared_sha256']);x=read_wav(base/manifest['original'])
        if sum(x*x)<=np.finfo(float).eps:raise ValueError('Silent source')
        regions=select_regions(x);manifest['regions']=regions
        manifest['region_annotation_note']='Reference-only automatic acoustic proxies; not human-verified phonetic ground truth.'
        # Same annotations are supplied to MATLAB, no codec-specific selection.
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n');all_manifests.append(manifest)
        directory=output/manifest['utterance'];directory.mkdir()
        reference_spectra=[stft(x,c) for c in CONFIGS]
        reference_region_plot(x,regions,directory/'reference_regions.png')
        for entry in manifest['conditions']:
            assert_hash(base/entry['decoded'],entry['decoded_sha256']);assert_hash(base/entry['encoded'],entry['encoded_sha256'])
            y=read_wav(base/entry['decoded'])
            if len(x)!=len(y):raise ValueError('Sample count mismatch')
            nmse,sdr=waveform_metrics(x,y);duration=len(x)/RATE
            measured=8*(base/entry['encoded']).stat().st_size/duration/1000
            row={'utterance':manifest['utterance'],'speaker':manifest['corpus']['speaker'],
                 'corpus_sex_label':manifest['corpus']['corpus_sex_label'],'codec':entry['codec'],
                 'nominal_kbps':entry['nominal_kbps'],'measured_kbps':measured,'duration_seconds':duration,
                 'nmse':nmse,'si_sdr_db':sdr,'stoi':float(stoi(x,y,RATE,extended=False)),
                 'encode_seconds':entry['encode_seconds'],'decode_seconds':entry['decode_seconds'],
                 'real_time_factor':(entry['encode_seconds']+entry['decode_seconds'])/duration,
                 'peak_original':float(np.max(np.abs(x))),'peak_decoded':float(np.max(np.abs(y))),
                 'full_scale_decoded_samples':int(np.sum(np.abs(y)>=1)),
                 'reference_sha256':manifest['prepared_sha256']}
            normalised=[]
            for config,(X,_) in zip(CONFIGS,reference_spectra):
                Y,_=stft(y,config);log_db,conv,score=spectral_error(X,Y)
                row[config[0]+'_log_db']=log_db;row[config[0]+'_convergence']=conv
                row[config[0]+'_normalised']=score;normalised.append(score)
            row['mr_error']=float(np.mean(normalised));rows.append(row)
            for region in regional_metrics(x,y,regions):
                region_rows.append({**region,'utterance':manifest['utterance'],'speaker':manifest['corpus']['speaker'],
                                    'codec':entry['codec'],'nominal_kbps':entry['nominal_kbps']})
            stem=f'{entry["codec"]}_{entry["nominal_kbps"]}k'
            condition_plots(x,y,reference_spectra,directory,stem,regions)
        print('Analysed',manifest['utterance'],'regions:',[r['type'] for r in regions],flush=True)
    if len(rows)!=48:raise ValueError(f'Expected 12 utterances x 4 conditions, obtained {len(rows)}')
    write_csv(output/'all_conditions.csv',rows);write_csv(output/'regions.csv',region_rows)
    grouped,differences,disagreements=aggregate(rows,region_rows,output)
    provenance={'analysis_runtime':'Python, not MATLAB','versions':{p:importlib.metadata.version(p) for p in ['numpy','scipy','matplotlib','pystoi']},
        'configs':CONFIGS,'utterances':len(all_manifests),'conditions':len(rows),
        'speaker_count':len(set(r['speaker'] for r in rows)),'source_bandwidth_note':'LibriSpeech sources are 16 kHz, resampled once to 24 kHz; information above 8 kHz is not original speech.',
        'region_method':'Automatic reference-only acoustic proxies; harmonicity, spectral flux, high-band energy; not forced alignment or phonetic ground truth.',
        'timing_limit':'Single serial end-to-end subprocess runs, including model/process startup; development workload not an isolated performance benchmark.',
        'bootstrap':'5000 paired speaker-cluster resamples, seed 5305; six speakers only; exploratory intervals, no multiple-comparison claims.',
        'manifests':all_manifests}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    lines=['# Real speech experiment — executed Python/SciPy analysis','',
        '12 LibriSpeech dev-clean utterances, six speakers, four actual codec conditions each. No model training.',
        '**These results were computed in Python/SciPy/pystoi, not MATLAB.** MATLAB Online verification remains separate.','',
        '| Codec | Target kb/s | Measured kb/s | SI-SDR dB | STOI | MR error | End-to-end RTF |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for r in grouped:
        lines.append(f'| {r["codec"]} | {r["nominal_kbps"]} | {r["measured_kbps_mean"]:.3f} | {r["si_sdr_db_mean"]:.3f} | {r["stoi_mean"]:.4f} | {r["mr_error_mean"]:.4f} | {r["real_time_factor_mean"]:.3f} |')
    lines+=['','## Diagnostic comparison',
        f'Medium-only versus MR changes the codec ordering in {sum(r["medium_vs_mr_ranking_changes"] for r in disagreements)} of {len(disagreements)} utterance/bitrate pairs.',
        f'Short- versus long-window log-magnitude errors disagree in ordering in {sum(r["short_vs_long_ranking_changes"] for r in disagreements)} of {len(disagreements)} pairs.',
        'These observed counts do not establish perceptual benefit or a new metric.','',
        '## Limitations',provenance['source_bandwidth_note'],provenance['region_method'],provenance['timing_limit'],provenance['bootstrap'],
        'Target rates are matched; container rates differ. Inspect measured rates before attributing differences to codec architecture.',
        'Speakers/utterances are a small deterministic development subset, not a representative population or a listening study.','',
        '![Spectral error](bitrate_spectral_error.png)','![Global measures](global_metrics.png)',
        '![Regional proxies](harmonic_transient.png)','![Runtime](quality_complexity.png)']
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('corpus',type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();analyse(args.corpus,args.output)
