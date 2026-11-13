#!/usr/bin/env python3
"""Package executed experiment evidence and attributable MATLAB Online data."""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path
import zipfile
import analyse_corpus as analysis


def read_csv(path):return list(csv.DictReader(path.open()))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('workspace',type=Path)
    parser.add_argument('--repo',type=Path,required=True);args=parser.parse_args()
    root=args.workspace;repo=args.repo;target=repo/'experiments'/'real_speech'
    target.mkdir(parents=True,exist_ok=False)
    for name in ['all_conditions.csv','summary.csv','regions.csv','paired_differences.csv',
                 'speaker_differences.csv','ranking_disagreements.csv','provenance.json','REPORT.md',
                 'bitrate_spectral_error.png','global_metrics.png','quality_complexity.png','harmonic_transient.png']:
        shutil.copy2(root/'python_reports'/name,target/name)
    for folder in ['rate_matched_opus','inband_sensitivity']:
        destination=target/folder;destination.mkdir()
        for name in ['all_conditions.csv','summary.csv']:shutil.copy2(root/folder/name,destination/name)
    controls=target/'rate_matched_opus'/'provenance';controls.mkdir()
    for file in sorted((root/'rate_matched_opus').glob('*/control_*.json')):
        shutil.copy2(file,controls/(file.parent.name+'_'+file.name))
    evidence=target/'validation';evidence.mkdir()
    for name in ['octave_core_tests.csv','octave_metrics.csv','numerical_parity.json','analysis_tests.log']:
        shutil.copy2(root/name,evidence/name)
    shutil.copy2(root/'alignment_checks.csv',target/'alignment_sensitivity.csv')
    data=target/'data_provenance';data.mkdir()
    for name in ['selection.csv','selection.json','LICENSE.txt']:shutil.copy2(root/'selected_speech'/name,data/name)
    case='1462-170138-0021'
    for codec in ['opus','encodec']:
        for kind in ['spectra','waveform']:
            shutil.copy2(root/'python_reports'/case/f'{codec}_6k_{kind}.png',target/f'representative_{codec}_6k_{kind}.png')
    manifest=json.loads((root/'real_codecs'/case/'manifest.json').read_text())
    x=analysis.read_wav(root/'real_codecs'/case/'original.wav')
    analysis.reference_region_plot(x,manifest['regions'],target/'representative_reference_regions.png')
    release=repo/'deliverables';release.mkdir(exist_ok=True);archive=release/'matlab_online_data.zip'
    if archive.exists():raise FileExistsError(archive)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        for folder in ['real_codecs','selected_speech','rate_matched_opus']:
            for file in sorted((root/folder).rglob('*')):
                if file.is_file():bundle.write(file,Path('experiment_data')/folder/file.relative_to(root/folder))
        bundle.writestr('experiment_data/ATTRIBUTION.txt',
            'LibriSpeech (c) 2014 by Vassil Panayotov; Creative Commons Attribution 4.0 International.\n'
            'Source: https://www.openslr.org/12/ ; https://creativecommons.org/licenses/by/4.0/\n'
            'See selected_speech/LICENSE.txt, selection.csv and selection.json for exact source IDs and selection.\n'
            'Adaptations: mono 24-kHz resampling and common -3 dB gain, then lossy Opus/EnCodec reconstructions.\n'
            'Codec tools: libopus via FFmpeg; Meta EnCodec 0.1.1 pretrained 24-kHz model. No model weights included.\n')
    core=read_csv(root/'octave_core_tests.csv');parity=json.loads((root/'numerical_parity.json').read_text())
    evidence_manifest={'data_zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'data_zip_bytes':archive.stat().st_size,'real_utterances':12,'speakers':6,'primary_codec_conditions':48,
        'additional_rate_matched_opus_conditions':24,'octave_reconstruction_cases':len(core),
        'maximum_reconstruction_absolute_error':max(float(r['max_absolute_error']) for r in core),
        'cross_runtime_numeric_comparisons':48*9,'parity':parity,
        'matlab_execution_verified':False,'python_stoi_implementation':'pystoi 0.4.1',
        'tested_m_functions':{name:hashlib.sha256((repo/'+codecdiag'/name).read_bytes()).hexdigest()
                              for name in ['analyse.m','synthesise.m','spectral_error.m','waveform_metrics.m','frame_mask.m']}}
    (target/'evidence_manifest.json').write_text(json.dumps(evidence_manifest,indent=2)+'\n')
    primary=read_csv(root/'python_reports'/'summary.csv');matched=read_csv(root/'rate_matched_opus'/'summary.csv')
    inband=read_csv(root/'inband_sensitivity'/'summary.csv');paired=read_csv(root/'python_reports'/'paired_differences.csv')
    selection=json.loads((root/'selected_speech'/'selection.json').read_text())
    region_counts={}
    for row in read_csv(root/'python_reports'/'regions.csv'):
        if row['codec']=='opus' and row['nominal_kbps']=='6':region_counts[row['type']]=region_counts.get(row['type'],0)+1
    text=['# Executed real-speech experiment results','',
          '**Analysis runtime: Python/SciPy/pystoi. Core `.m` functions also executed under GNU Octave. Native MATLAB tests, toolbox calls and rendering are NOT yet verified.**','',
          '## Data and protocol',
          f'LibriSpeech dev-clean: 12 utterances, six speakers, {selection["total_seconds"]:.2f} s total; source files are 16-kHz read English speech. Each prepared reference is mono 24 kHz with common -3 dB gain. No independent output gain fitting or local alignment is used.',
          'The archive matched the official MD5. Selection was deterministic and outcome-blind: first three eligible IDs per corpus F/M label, first two 4–10-s recordings per speaker in archive order. This is a small development subset, not a population-representative benchmark or a training-overlap audit.',
          'The same reference waveform goes to standard Opus and pretrained EnCodec at requested 6 and 12 kb/s. Versions, commands, source/output hashes, sample counts, clipping flags and timings are retained in provenance.','',
          '## Actual software validation',
          f'- {len(core)} exact-source STFT/ISTFT reconstruction cases under GNU Octave 10.3.0: maximum absolute error {evidence_manifest["maximum_reconstruction_absolute_error"]:.3g}; invalid NOLA rejected.',
          '- 48 real-speech conditions × nine numerical metrics compared between Python and the exact repository `.m` functions run in Octave: all 432 discrepancies below 1e-9; observed maximum below 8e-13.',
          '- Five independent Python numerical tests passed: SciPy STFT/frame parity at all scales, known waveform and spectral errors, hash tampering and STOI identity. The earlier four codec integration tests also passed.',
          '- 48 primary real codec outputs and 24 extra bitrate-matched Opus outputs were actually encoded/decoded. All primary outputs retained the reference sample count. The report does not assert that MATLAB Online ran.','',
          '## Primary requested-rate comparison',
          'Means over 12 utterances; SDs and availability are in summary.csv. STOI is a computational intelligibility-related reference, not a listening score.','',
          '| Codec | Target kb/s | File kb/s | SI-SDR dB | STOI | MR error | End-to-end RTF |',
          '|---|---:|---:|---:|---:|---:|---:|']
    for r in primary:
        text.append(f'| {r["codec"]} | {r["nominal_kbps"]} | {float(r["measured_kbps_mean"]):.3f} | {float(r["si_sdr_db_mean"]):.3f} | {float(r["stoi_mean"]):.4f} | {float(r["mr_error_mean"]):.4f} | {float(r["real_time_factor_mean"]):.3f} |')
    text+=['','![Global metrics](global_metrics.png)','![Three spectral scales](bitrate_spectral_error.png)','',
           '## Actual-rate-matched sensitivity control',
           'Opus includes more container overhead. To avoid treating equal targets as equal actual rates, choose an Opus CBR request from three adjacent 400-bps settings using encoded size only. No quality outcome is used to select the request. The EnCodec output stays unchanged.','',
           '| EnCodec rate class | Opus file kb/s | EnCodec file kb/s | Mean relative gap | Opus SI-SDR | EnCodec SI-SDR | Opus STOI | EnCodec STOI | Opus MR | EnCodec MR |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in matched:
        text.append(f'| {r["comparison_bandwidth_kbps"]} | {float(r["opus_measured_kbps_mean"]):.3f} | {float(r["encodec_measured_kbps_mean"]):.3f} | {100*float(r["mean_relative_pair_rate_gap"]):.2f}% | {float(r["opus_si_sdr_db_mean"]):.3f} | {float(r["encodec_si_sdr_db_mean"]):.3f} | {float(r["opus_stoi_mean"]):.4f} | {float(r["encodec_stoi_mean"]):.4f} | {float(r["opus_mr_error_mean"]):.4f} | {float(r["encodec_mr_error_mean"]):.4f} |')
    text+=['','The mean ordering by SI-SDR and MR error is retained in this size-matched control. The small 12-kb/s STOI ordering changes: this prevents a robust claim that nominal-rate Opus has higher intelligibility. A lower requested Opus rate does not improve every metric monotonically; do not assume monotonic quality or infer its cause from these data alone.','',
           '## Frequency-band sensitivity',
           'The original source is 16 kHz: 24-kHz resampling does not create original speech information above 8 kHz. Repeat spectral evaluation over 0–8 kHz and report 4–8-kHz energy changes separately.','',
           '| Design | Codec | Rate class | 0–8-kHz MR error | Mean 4–8-kHz energy ratio (dB) |',
           '|---|---|---:|---:|---:|']
    for r in inband:
        text.append(f'| {r["design"]} | {r["codec"]} | {r["comparison_bandwidth_kbps"]} | {float(r["inband_mr_error_mean"]):.4f} | {float(r["decoded_4_to_8k_energy_ratio_db_mean"]):.2f} |')
    text+=['','The mean MR ordering remains after restricting the analysis to original-source bandwidth. At the 6-kb/s rate class, Opus attenuates 4–8-kHz energy more strongly than EnCodec on this subset; this describes band energy, not necessarily perceived quality or true fricative identity. At 12 kb/s, SI-SDR favours EnCodec while spectral diagnostics favour Opus: one scalar does not describe every signal property.','',
           '## Multi-resolution modification and regional evidence',
           'Compare a medium-only diagnostic with the three-resolution score while holding data/codecs fixed. In the primary experiment there were **0/24 medium-versus-MR ranking changes** and **0/24 short-versus-long log-error ranking changes**. Thus this subset provides no evidence that extra resolutions improve overall codec ranking. Do not invent a positive result.',
           f'Reference-only heuristics selected {region_counts.get("harmonic",0)} harmonic proxies, {region_counts.get("transient",0)} transient proxies and {region_counts.get("fricative",0)} high-frequency/fricative proxies. They are acoustic proxies, not human phonetic annotations. Missing fricative candidates are retained as missing, not forced.',
           'Detector details: 25-ms frames/10-ms hop; energy gate at 4% of maximum frame power; lag-normalised autocorrelation over 60–300 samples (80–400 Hz); 200-ms smoothing; harmonic score threshold 0.55; fricative proxy uses 4–8-kHz energy, periodicity <0.5 and score threshold 0.035; transient proxy maximises positive spectral flux. Regions are fixed before inspecting codec errors.',
           '![Reference regions](representative_reference_regions.png)',
           '![Opus 6k](representative_opus_6k_spectra.png)','![EnCodec 6k](representative_encodec_6k_spectra.png)','',
           '## Paired uncertainty',
           'Differences below are EnCodec minus Opus for primary requested-rate conditions. Bootstrap resamples six speaker clusters (two utterances each), 5000 times, seed 5305. These are exploratory 95% intervals on a small fixed subset, not population guarantees or corrected significance tests.','',
           '| Target | Metric | Mean paired difference | Speaker-cluster interval |',
           '|---|---|---:|---|']
    for r in paired:
        if r['metric'] in ['si_sdr_db','stoi','mr_error']:
            text.append(f'| {r["nominal_kbps"]} | {r["metric"]} | {float(r["encodec_minus_opus"]):.4f} | [{float(r["speaker_cluster_ci95_low"]):.4f}, {float(r["speaker_cluster_ci95_high"]):.4f}] |')
    text+=['','## Runtime and limitations',
           'RTF is serial same-machine CPU subprocess wall time including process/model loading and file I/O. Model download is excluded. Neural torch threads are 1. This is a single-pass implementation measurement under a development workload, not an isolated or steady-state inference benchmark. No paper runtime is directly compared.',
           '![Implementation cost](quality_complexity.png)',
           'Additional limitations: six speakers, English read speech only, no listening study, no training-overlap audit, heuristic regions, no native MATLAB UI/toolbox execution, fixed score weights/floors, no packet loss and no neural-enhanced Opus condition. Spectral magnitudes ignore phase; SI-SDR ignores scale/polarity. These limits explain why a universal codec winner is not supported.','',
           '## Reproduction',
           'See repository README, scripts/select_speech.py, run_corpus.py, analyse_corpus.py, rate_matched_control.py, inband_sensitivity.py and the downloadable MATLAB Online data ZIP. Dataset attribution and exact IDs are in data_provenance. Source-code acknowledgements and course AI-use declarations remain required.']
    alignment=read_csv(root/'alignment_checks.csv')
    alignment_text=['## Global-lag sensitivity (primary conditions only)','',
        'A ±50-ms full-utterance cross-correlation search found best lags between -3 and +1 samples (maximum 0.125 ms at 24 kHz). EnCodec had a zero best lag in all 24 cases. These are inferred correlation lags, not independently measured codec delays.',
        'Primary scores and WAVs remain unshifted; only this supplementary check trims a single constant lag. No regional time warping is used.','',
        '| Codec | Target kb/s | Mean raw SI-SDR dB | Mean best-global-lag SI-SDR dB | Maximum absolute lag (samples) |',
        '|---|---:|---:|---:|---:|']
    for codec in ['opus','encodec']:
        for bitrate in [6,12]:
            subset=[r for r in alignment if r['codec']==codec and int(r['nominal_kbps'])==bitrate]
            raw=np_mean(subset,'unaligned_si_sdr_db');shifted=np_mean(subset,'global_lag_sensitivity_si_sdr_db')
            lag=max(abs(int(r['best_global_lag_samples'])) for r in subset)
            alignment_text.append(f'| {codec} | {bitrate} | {raw:.3f} | {shifted:.3f} | {lag} |')
    alignment_text+=['','At 12 kb/s the inferred constant-lag adjustment raises Opus SI-SDR substantially, so the raw margin must not be described entirely as codec waveform damage. EnCodec still has higher mean SI-SDR in this primary lag-sensitivity check. Rate matching and lag sensitivity were separate checks; their combined effect has not been evaluated.','']
    body='\n'.join(text)+'\n'
    body=body.replace('## Multi-resolution modification and regional evidence',
        '\n'.join(alignment_text)+'\n## Multi-resolution modification and regional evidence')
    (target/'RESULTS.md').write_text(body)
    print(json.dumps(evidence_manifest,indent=2))


def np_mean(rows,key):return sum(float(r[key]) for r in rows)/len(rows)


if __name__=='__main__':main()
