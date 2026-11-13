# Initial implementation audit — 13 November 2026

The first implementation was not end-to-end validated. This audit found and
corrected concrete defects; a clean syntax tree must not be described as proof
that MATLAB numerical results or reports are correct.

| Finding | Impact | Correction / regression coverage |
| --- | --- | --- |
| MATLAB local tests lacked `test` prefixes | `functiontests(localfunctions)` could discover no tests | Rename all test functions; `run_project_tests` requires >=8 discovered tests and every test passing |
| Spectral averages included frames centred in artificial padding | Silence outside the recording could dilute errors differently across scales | Shared frame-centre mask in global and regional metrics and plots; MATLAB mask regression test |
| Hashes were recorded but not checked by MATLAB | Modified files could retain stale experiment provenance | Stream SHA-256 from actual files; reject mismatched reference/decoded/bitstream metadata; known-hash/tampering tests |
| Corpus checks used only utterance names and machine metadata | Renamed duplicate audio or incompatible timing scopes could be pooled | Reject duplicate reference hashes; match durations; require matching runtime scope and software metadata for complexity plots |
| Equal target bitrate could be mistaken for equal actual bitrate | Headers can distort comparisons, especially for short clips | Require measured rates; record paired relative rate gap and warn above a declared 10% threshold |

The corrected MATLAB tests also check known metric behaviour: amplitude scaling
changes NMSE but not SI-SDR, and polarity inversion leaves magnitude-only
spectral error unchanged while producing waveform/complex-STFT error. These
are important limits of the metrics, not bugs to hide.

## Executed evidence

- Four Python integration tests passed with the neural test enabled, including
  actual official pretrained EnCodec and libopus round trips at both 6/12 kb/s.
- The tests use synthetic fixtures and exercise real packed bitstreams,
  sample counts, finite/nonzero decoded output, bytes/rate calculation, hashes,
  silence rejection, overwrite protection and preservation of float overshoots.
- All 16 MATLAB files parse using the tree-sitter MATLAB grammar. This is a
  static check, not MATLAB's test discovery, numerical execution or rendering.

## Remaining evidence gap

MATLAB cannot start in the current cloud machine without activation. The user
chose MATLAB Online. Thus the eight MATLAB tests, STFT reconstruction tolerance,
COLA toolbox calls, SHA-256 JVM integration, STOI calls, plotting and corpus
aggregation still require a real MATLAB run. Run `run_project_tests` in the
project directory and inspect failures before interpreting real speech data.

No multi-speaker dataset has been processed and no claim of codec superiority,
speech intelligibility, perceptual quality or steady-state computational cost
is supported yet. The software is an initial research implementation with a
tested codec-preparation path and an unexecuted MATLAB analysis path.
