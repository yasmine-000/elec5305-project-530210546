# Experiment protocol and instructor-feedback mapping

The instructor feedback supplied by the student on 13 November 2026 revises
the original proposal into a speech-codec diagnostic study. This document
records research requirements, not measured findings.

## Core experiments

0. Validate explicit windowing, FFT, inverse FFT and weighted overlap-add.
   Check periodic Hann windows at 75% overlap using MATLAB `iscola(...,'wola')`.
   Test random, impulse/boundary, short constant and silent signals, with two
   FFT sizes at each resolution. Require max absolute error <1e-10. Reject a
   deliberately invalid non-overlapping Hann/NOLA condition.
1. Use 12, 28 and 56 ms windows, respectively 288, 672 and 1344 samples at
   24 kHz. Hop is L/4; FFT is the next power of two. FFT zero padding increases
   sampling density, not physical resolving capability. `demonstrate_zero_padding`
   contrasts short-window FFT lengths with a longer physical window.
2. Prepare each source once: mono, 24 kHz, common fixed -3 dB gain, float WAV.
   Feed this identical reference to every codec. Save its SHA-256 hash.
3. Encode Opus at 6/12 kb/s CBR, 20-ms frames, VoIP application. Decode with
   FFmpeg's `libopus` decoder. Record exact commands and library version.
4. Use pretrained mono EnCodec 24 kHz at 6/12 kb/s, CPU, without optional
   language-model entropy coding. Save actual packed `.ecdc` files, not tensor
   sizes. Do not train a model. Validate this path before collecting results.
5. Generate a diagnostic report for each utterance. Annotate stable voiced,
   transient and fricative intervals from the clean reference before comparing
   codecs, and keep the same intervals across all four conditions.
6. Repeat across 10–20 utterances and several speakers, with acoustic variety.
   Preserve a manifest of corpus IDs, speaker IDs, data split and chosen regions.
   Summarise paired means and variability, and discuss representative failures.

## Equations and safeguards

The analysis is the full complex FFT of each windowed frame. One full window
of zeros is padded on both boundaries, and the final frame is padded to a full
hop. Synthesis multiplies inverse-FFT frames by the same window and divides
the overlap-add signal by the accumulated squared-window weights. All retained
samples must have positive weights (NOLA). Padding is removed only afterward.
`iscola(...,'wola')` verifies constant overlap weights for chosen configurations.
For scoring and visualisation, retain only frames whose centres lie inside
the actual waveform duration. Boundary support is still zero padded, but
padding-only frame centres must not dilute log-magnitude averages. Short/long
regional scores use this same rule.

For reference STFT X and decoded STFT Y at each scale:

- Spectral convergence = ||abs(Y)-abs(X)||F / max(||abs(X)||F, eps).
- Log-magnitude error = mean absolute dB difference, with both magnitudes
  floored at max(max(abs(X))*1e-5, eps), a shared reference-relative -100 dB floor.
- Normalised scale error = 0.5 * (log-magnitude error / 100 + convergence).
- Multi-resolution diagnostic error = arithmetic mean of the three scale errors.

The equal weighting is a declared engineering choice, not a fitted perceptual
model. The score is unbounded and depends on framing/floors. Do not interpret
small differences as perceptual significance. Quiet/silent bins and padding
affect the spectral measures; keep exactly the same settings across conditions.

Waveform NMSE is sum((decoded-reference)^2)/sum(reference^2), without gain
fitting. SI-SDR first removes each signal's mean, projects the decoded signal
onto the reference, then compares projected energy with residual energy.
Perfect reconstruction gives +Inf; a zero projected target gives -Inf.
Do not substitute large finite scores or silently drop infinities in reporting.
JSON serialises nonfinite values as null; CSV retains them and is the primary
numerical results format.

STOI uses MathWorks `stoi(processed,reference,fs)` when Audio Toolbox is
available; missing STOI remains NaN with an availability flag. STOI is an
intelligibility reference, not proof of listening quality. No formal listening
study is claimed.

Region diagnostics use the exact same reference-selected intervals for all
conditions. Local NMSE, short/long log-spectral error, peak-absolute-amplitude
time difference, energy ratio, and above-4-kHz STFT energy ratio are exported.
Peak timing is meaningful primarily for an isolated transient; it is not an
F0 tracker or general speech-alignment algorithm. A long-window plot is the
starting point for inspecting individual harmonics; no automatic pitch-tracking
claim is made. Compare high-frequency fricative energy alongside the plots.

Codec output is float WAV, preserving samples beyond full scale for detection.
Do not independently normalise outputs. A declared nonnegative delay can be
removed for external reconstructions, with sample counts recorded. Do not
cross-correlate each small region to remove codec-induced transient errors.
The generated codec path requires exact gapless decoded sample counts; investigate
any mismatch rather than padding to make a metric run.
Compute each actual input hash before analysis and reject supplied reference,
decoded or bitstream hashes that disagree. Corpus aggregation also rejects a
duplicate reference hash under another utterance name.

## Bitrate and timing

Measured kb/s = 8 * actual encoded-file bytes / source duration / 1000.
Include Ogg or EnCodec headers consistently. This is **container bitrate**, not
raw codec payload rate. Short clips may substantially exceed requested rates
because of headers, frame rounding, and padding. Plot measured rates and disclose
both nominal and measured values; an equal target is not proof of equal measured
bitrate. Use sufficiently long utterances and flag large measured mismatches.
Aggregation records abs(Opus rate - EnCodec rate)/mean(the two rates). Differences
above 10% produce a warning; 10% is a transparent screening threshold, not a
perceptual-equivalence standard. Missing measured bitstream rates block aggregation.

RTF = (encoding wall seconds + decoding wall seconds) / audio duration. The
baseline times include subprocess start, model loading from the local cache,
bitstream packing and file I/O. Model download/cache priming is outside timing.
These are **end-to-end implementation timings**, not steady-state neural-kernel
benchmarks or algorithmic complexity estimates. EnCodec CPU torch threads are
set to 1; FFmpeg's commands and hardware metadata are recorded. There is no GPU.
Use the same machine and environment for both codecs; repeat runs to quantify
timing variation and use long recordings. Do not compare these times directly
with numbers quoted in papers. CPU cold-cache/startup effects remain limitations.
Quality/complexity plots require matching host/hardware, Python/tool/codec
environment metadata and timing scope. Matching metadata cannot remove startup
or operating-system scheduling effects; report those limitations.

## Opus neural-enhancement condition

The initial development machine has FFmpeg 7.1.5 and libopus 1.5.2. In
[libopus 1.5.2 opus_decoder.c](https://github.com/xiph/opus/blob/v1.5.2/src/opus_decoder.c),
decoder complexity initialises to 0; neural PLC/LACE/NoLACE require raised
complexity (5/6/7). FFmpeg's libopus wrapper does not raise this control. Thus
the verified baseline requests no optional neural enhancement. No packet loss
or FEC experiment is included.

This does not assert that every current Opus build is purely conventional.
The baseline version is pinned in experiment provenance, not claimed to be the
newest release. If replacing it with Opus 1.6 or another build, verify its
defaults and optional neural controls before collecting data. Neural Opus is
an optional later extension, not part of the initial minimum experiment.

## Deliverable coverage and remaining research

| Feedback requirement | Implementation / next step |
| --- | --- |
| STFT/ISTFT validation, COLA/NOLA | `validate_stft.m`, MATLAB tests (must run online) |
| Three physical resolutions, zero padding | `settings.m`, `demonstrate_zero_padding.m` |
| Same clean speech for paired codecs | `prepare_codecs.py`, reference hash and checks |
| Actual bitstreams and measured bitrate | `.opus`/`.ecdc`, bytes/duration in manifest |
| Multi-resolution and waveform metrics | `run_diagnostic.m`, SI-SDR/NMSE and optional STOI |
| Harmonic/transient/fricative comparison | Manually annotated regions, local metrics and plots |
| Cost, reports, variability and figures | Manifest timings, per-utterance report, `summarise_reports.m` |
| Real multi-speaker experiment and conclusions | Not yet performed; requires clean speech, EnCodec validation and MATLAB execution |

The current repository intentionally contains no invented result tables,
speech-quality claims, pretrained weights, copied restricted corpus audio or
claimed perceptual metric. Synthetic fixtures are labelled as such. A GUI,
neural Opus extension, very-low-bitrate 3 kb/s condition, trained models and
automatic region detection are outside the initial scope.
