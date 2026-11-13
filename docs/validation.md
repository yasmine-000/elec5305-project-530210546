# Validation status

Initial development validation, 13 November 2026:

- Python 3.12; FFmpeg 7.1.5; installed system libopus 1.5.2.
- Three real Python/FFmpeg integration tests: paired 6/12 kb/s Opus round trips
  and measured bytes/rate, silent-input rejection, and float-WAV overshoot
  preservation/detection. The paired test also verifies 48-to-24-kHz/stereo-to-mono
  conversion, exact non-frame-aligned sample count, hashes, manifest persistence
  and protection against output-directory overwrite.
- MATLAB files are checked using a MATLAB tree-sitter grammar. This is a syntax
  check only; it cannot establish numerical or toolbox/API correctness.

Not yet executed:

- `validate_stft`, `runtests('tests/test_core.m')`, `demo_project`, report plots
  and corpus aggregation under MATLAB. The local R2025a installation cannot
  start without a licence; the intended execution target is MATLAB Online.
- EnCodec/PyTorch installation, model download and neural bitstream round trips.
- STOI, real speech data analysis, multi-speaker comparisons or listening tests.

The Python fixtures are synthetic and are not codec-quality research results.
Do not cite their very short clip bitrate or runtime as representative of speech.
The MATLAB tests are supplied for the next MATLAB Online run; writing them does
not imply they have passed. Record any failures before interpreting project data.
