# Multi-Resolution Analysis of Speech Codec Artefacts

**ELEC5305 — Opus versus pretrained EnCodec, with MATLAB diagnostics.**

Research question: *At comparable low bitrates, how do Opus and EnCodec differ
in their preservation of transient, harmonic and spectral speech information,
and which STFT resolutions reveal these differences?*

This implements the revised direction in the instructor's feedback. It is an
initial research software implementation, **not a completed codec comparison**.
There are no measured speech results or claims that one codec is better.
The original proposal PDF is retained as historical context; the revised
[experiment protocol](docs/protocol.md) describes the current project.

## Start in MATLAB Online

1. Sign in at [MATLAB Online](https://matlab.mathworks.com/) with your own
   university MathWorks account. Use R2025a if your account offers it.
2. Download this repository using GitHub **Code → Download ZIP**, extract it,
   and upload the project folder to MATLAB Drive. Alternatively use MATLAB's
   supported Git integration. Cloud workspace files do not sync automatically.
3. Open the project folder as MATLAB's current folder. Run:

```matlab
version
ver signal
validate_stft                    % Experiment 0: 24 reconstruction cases
results = runtests('tests/test_core.m');
assertSuccess(results)
demo_project                    % Synthetic fixture, NOT speech/codec results
demonstrate_zero_padding         % Physical resolution versus FFT sampling
```

These commands create CSV tables, PNG figures and a Markdown report under
`results/`. Use a new output directory to rerun a demo/report; existing outputs
are protected against accidental overwrite.

Requirements: MATLAB R2025a, Signal Processing Toolbox (`iscola`), and optionally
Audio Toolbox (`stoi`). If STOI is unavailable it is explicitly marked
`NaN`/`unavailable`, never replaced by a fake score. EnCodec runs in Python;
there is no neural-network training or Python requirement for MATLAB analysis.

**Validation status:** Python/Opus integration tests have run in the development
environment. MATLAB source has passed a syntax-tree check, but MATLAB tests,
figure rendering, MATLAB Online operation and pretrained EnCodec inference
remain unverified. See [validation evidence](docs/validation.md).

## Prepare real paired codec reconstructions

Use your own computer or the development cloud terminal, not MATLAB Online's
command window. Install Python 3.10–3.12 and FFmpeg with both the `libopus`
encoder and decoder. The Opus-only path uses the Python standard library:

```bash
python scripts/prepare_codecs.py data/speech.wav \
  --output results/codecs/utterance01 --codecs opus
```

For the full comparison, install Meta EnCodec and matching CPU PyTorch packages
in a virtual environment. Example for Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.5.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r scripts/requirements-neural.txt
python scripts/prepare_codecs.py data/speech.wav \
  --output results/codecs/utterance01 --codecs opus encodec --bitrates 6 12
```

The neural environment recipe and inference path have not yet been executed
here. First use requires downloading the official pretrained model from
`dl.fbaipublicfiles.com`; use the environment's approved network configuration
if this destination is blocked. Do not disable TLS verification.

The script prepares **one shared 24-kHz mono reference**, with a fixed -3 dB
gain for headroom. It records the command and hash, encodes real `.opus` and
`.ecdc` bitstreams, decodes to float WAV, checks sample counts/rate/channels,
and saves `manifest.json`. No independent decoded gain normalisation, implicit
time alignment or PCM clipping is applied. Target bitrates are 6 and 12 kb/s;
measured bitrate includes the full encoded container/header.

The reference and decoded WAVs, bitstreams and manifest must all be copied to
MATLAB Drive together. Then run:

```matlab
run_diagnostic('results/codecs/utterance01/manifest.json', ...
               'results/reports/utterance01');
```

For speech-structure analysis, add reference-selected regions to the manifest
**before** generating the report. Times below illustrate the schema only; choose
actual vowel, plosive and fricative boundaries from your own clean utterance:

```json
"regions": [
  {"type": "harmonic",  "start_seconds": 0.20, "end_seconds": 0.45},
  {"type": "transient", "start_seconds": 0.55, "end_seconds": 0.63},
  {"type": "fricative", "start_seconds": 0.80, "end_seconds": 1.00}
]
```

Manifests can also describe external reconstructions: supply `utterance`,
`original`, and a `conditions` array with `codec`, `nominal_kbps`, and `decoded`.
Paths are relative to the manifest. Optional `encoded`, `encode_seconds`,
`decode_seconds`, and nonnegative `delay_samples` provide bitrate/runtime and
an explicitly known delay correction. Missing bitrate/runtime become `NaN`.
For external WAVs, standardise to 24-kHz mono *before* this step. The analyser
rejects short decoded signals; it records any explicitly removed delay and
trimmed excess tail rather than silently padding.

## Outputs and interpretation

- `summary.csv`: encoded size, measured bitrate, runtime/RTF, NMSE, SI-SDR,
  STOI availability, three spectral errors, multi-resolution score, peaks,
  full-scale sample counts, and length/delay bookkeeping.
- `condition_*_spectra.png`: original, decoded, complex-error STFT and signed
  log-magnitude difference, at short/medium/long resolutions.
- `condition_*_waveforms.png`: paired waveforms and decoded-minus-original error.
- `regions.csv`: local error, short/long spectral errors, absolute-peak timing,
  energy ratio and above-4-kHz energy ratio for supplied speech regions.
- `report.md` and `provenance.json`: condition overview, figures, settings,
  MATLAB/toolbox versions and the original manifest.

Short windows expose rapid changes; long windows expose harmonic detail. The
score is a transparent diagnostic summary, **not a new perceptual metric**.
SI-SDR/STOI are reference measures and do not replace regional analysis.
Full-scale sample flags indicate possible clipping/overshoot, not proof that
an encoder internally clipped. See the protocol for equations and limitations.

After collecting complete paired results for 10–20 utterances across speakers:

```matlab
summarise_reports(["results/reports/utterance01", ...
                   "results/reports/utterance02"], 'results/aggregate');
```

This requires all four conditions per utterance, rejects duplicate utterances,
and exports means, SDs, available-value counts, bitrate/error plots, metric
comparisons, annotated harmonic/transient comparisons, and quality/complexity
plots when hardware metadata matches. Region plots require supplied annotations.
No statistical significance or codec ranking is assumed in advance.

## Files and tests

| File | Purpose |
| --- | --- |
| `+codecdiag/` | Explicit STFT/WOLA synthesis and signal metrics |
| `validate_stft.m` | COLA/NOLA and near-perfect reconstruction validation |
| `run_diagnostic.m` | Per-utterance report for real decoded WAVs |
| `summarise_reports.m` | Paired-corpus summaries and engineering figures |
| `demo_project.m` | Deterministic synthetic pipeline fixture |
| `demonstrate_zero_padding.m` | Two-tone zero-padding demonstration |
| `scripts/prepare_codecs.py` | Standardisation, real codec bitstreams and provenance |
| `tests/` | MATLAB numerical/report tests and Python/FFmpeg integration tests |
| `data/README.md` | Speech selection, rights and preparation checklist |

Run the Python tests with FFmpeg installed:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Dataset audio, generated reports and model weights are intentionally excluded
from Git. Never commit account passwords, activation files or private recordings.

## References

- Allen & Rabiner, “A unified approach to short-time Fourier analysis and
  synthesis,” *Proceedings of the IEEE*, 1977.
- Harris, “On the use of windows for harmonic analysis with the discrete Fourier
  transform,” *Proceedings of the IEEE*, 1978.
- Griffin & Lim, “Signal estimation from modified short-time Fourier transform,”
  *IEEE TASSP*, 1984.
- Rabiner & Schafer, *Theory and Applications of Digital Speech Processing*, 2011.
- [Opus / RFC 6716](https://www.rfc-editor.org/rfc/rfc6716),
  [official implementation](https://opus-codec.org/),
  [Opus 1.5 neural enhancements](https://opus-codec.org/demo/opus-1.5/).
- Défossez et al., [High Fidelity Neural Audio Compression](https://arxiv.org/abs/2210.13438),
  2022/2023; [official EnCodec implementation](https://github.com/facebookresearch/encodec).
- [Speech Quality Evaluation of Neural Audio Codecs](https://www.isca-archive.org/interspeech_2024/),
  Interspeech 2024 (instructor-recommended reading; locate the paper in the proceedings).
- Taal et al., “An algorithm for intelligibility prediction of time-frequency
  weighted noisy speech,” *IEEE TASLP*, 2011 (STOI).
- Le Roux et al., [SDR – Half-baked or Well Done?](https://arxiv.org/abs/1811.02508),
  ICASSP 2019 (SI-SDR).
- [LibriSpeech](https://www.openslr.org/12/) clean speech corpus.
