# Validation status

Development and audit validation, 13 November 2026:

- Python 3.12; FFmpeg 7.1.5; installed system libopus 1.5.2.
- Three real Python/FFmpeg integration tests: paired 6/12 kb/s Opus round trips
  and measured bytes/rate, silent-input rejection, and float-WAV overshoot
  preservation/detection. The paired test also verifies 48-to-24-kHz/stereo-to-mono
  conversion, exact non-frame-aligned sample count, hashes, manifest persistence
  and protection against output-directory overwrite.
- Official EnCodec 0.1.1 with CPU torch/torchaudio 2.5.1+cpu, numpy 2.5.4 and
  einops 0.8.2 was installed. The official pretrained 24-kHz checkpoint was
  downloaded through the library's normal hash-checked loading path.
- An additional opt-in integration test ran actual Opus and EnCodec bitstream
  encode/decode at 6 and 12 kb/s on the same non-frame-aligned synthetic input.
  All four conditions retained the reference sample count, produced nonzero
  finite output and matching file hashes. Total test run: **4 passed**, none
  skipped, using `CODECDIAG_TEST_NEURAL=1`. These are not speech-quality findings.
- MATLAB files are checked using a MATLAB tree-sitter grammar. This is a syntax
  check only; it cannot establish numerical or toolbox/API correctness.

Real-speech experiment subsequently executed on the same date:

- Official LibriSpeech dev-clean archive MD5 verified; 12 utterances, six speakers,
  82.33 seconds, selected by fixed duration/ID rules without codec outcomes.
- 48 primary real codec conditions and 24 additional file-rate-matched Opus
  controls encoded/decoded; source/output hashes and sample counts checked.
- Five independent Python analysis tests passed (actual log in the evidence
  folder), including framing/FFT parity with SciPy and analytic metric values.
- Exact repository `.m` analysis/synthesis code ran in GNU Octave 10.3.0 for
  60 reconstruction cases: maximum error 1.3322676295501878e-15; invalid NOLA
  rejected and known metric checks passed.
- Exact `.m` STFT/waveform/spectral functions ran in Octave for all 48 actual
  speech codec outputs. Python and Octave agreed for 432 numeric values, with
  maximum discrepancy below 8e-13 (declared tolerance 1e-9).
- STOI was computed using **pystoi 0.4.1**, not a MathWorks toolbox execution.
  Automatic reference-only regions are labelled acoustic proxies, not human
  phonetic ground truth. Rate and original-source-bandwidth controls were run.
- Full numeric tables, source provenance, figures, test logs and parity evidence
  are in `../experiments/real_speech/`. Data ZIP includes actual reference/output
  audio and bitstreams with dataset attribution.

Not yet executed:

- `validate_stft`, `run_project_tests`, `demo_project`, report plots
  and corpus aggregation under MATLAB. The local R2025a installation cannot
  start without a licence; the intended execution target is MATLAB Online.
- Native MathWorks STOI, JVM hash verification and report/table/graphics APIs.
- Formal listening tests, population-representative evaluation or a training
  overlap audit. None is implied by the small development subset.

The Python fixtures are synthetic and are not codec-quality research results.
Do not cite their very short clip bitrate or runtime as representative of speech.
The MATLAB tests are supplied for the next MATLAB Online run; writing them does
not imply they have passed. Record any failures before interpreting project data.
