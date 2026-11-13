# Multi-Resolution Analysis of Speech Codec Artefacts: Opus versus EnCodec

**Working report template — not a completed submission.** Replace bracketed
prompts with verified content. Do not submit placeholder results or convert
unexecuted methods into past-tense claims.

Author: [student details]
Course: ELEC5305
Date/version: [final date and tested commit]

- Project code: https://github.com/yasmine-000/elec5305-project-530210546
- GitHub Site: [add the published site URL; a repository link alone is not the site]
- Demonstration video: [add the real accessible video URL]

## Contents

[Generate a contents page with section/subsection links and page numbers in the
final report editor. Confirm link functionality after export.]

## Abstract

[Summarise the question, method, actual data, principal observed findings and
limits. Write this after the results; do not predict which codec will win.]

## 1. Introduction and research question

**Primary question:** At comparable low bitrates, how do Opus and pretrained
EnCodec differ in their preservation of transient, harmonic and spectral speech
information, and which STFT resolutions reveal these differences?

[Motivate low-bitrate speech communication. Explain why a single global metric
or one visually attractive spectrogram cannot answer the whole question. Link
the question to literature, define the scope and state the intended contribution.]

## 2. Literature review

### 2.1 STFT, overlap-add and physical time/frequency resolution

[Analyse Allen & Rabiner, Harris and relevant reconstruction work. Explain
window length versus zero padding, COLA/NOLA, and why unchanged valid STFT
reconstruction is a validation task rather than the main research finding.]

### 2.2 Conventional and neural audio coding

[Analyse the Opus standard/implementation, EnCodec's primary paper and a direct
neural-codec comparison. Compare coding approaches, low-rate trade-offs,
availability, complexity and model limitations. Do not claim every current
Opus decoder is purely non-neural; identify the experimental configuration.]

### 2.3 Evaluation and choice of method

[Compare SI-SDR, STOI and multi-resolution spectral diagnostics. Explain what
each can/cannot establish. Justify the chosen codecs, bitrates, reference
format and analysis scales against alternatives. Identify the gap addressed
by this project and explicitly cite the sources supporting the rationale.]

### 2.4 Concepts and unknowns learned

[Describe the concepts you personally had to learn and questions that arose
from reading. Use specific explanations tied to actual sources and experiments;
do not invent a personal learning history.]

## 3. Methods

Clearly separate **intended design** from **completed implementation and runs**.
Use `docs/protocol.md` for implementation detail, but justify choices using
primary literature rather than citing your own code as scientific evidence.

### 3.1 Data and preparation

[Corpus, rights, utterance/speaker selection, development/evaluation distinction,
sample counts/durations, resampling, mono conversion, common gain and exclusions.
Record dataset IDs and reference-selected region annotations.]

### 3.2 Experiment 0: implementation validation

[Window/hop/FFT settings, weighted COLA check, boundary treatment, NOLA rejection,
test discovery and numerical tolerance. Record actual MATLAB/toolbox versions
and test logs. Distinguish synthetic fixtures from speech data.]

### 3.3 Paired codec experiment

[Exact versions/commands, Opus enhancement configuration, official EnCodec model,
6/12 kb/s targets, actual container rates, same input, sample-count/delay checks,
clipping/overshoot handling, hashes, CPU/hardware and timing scope.]

### 3.4 Diagnostic measures and regional analysis

[Define NMSE, zero-mean SI-SDR, STOI if available, spectral convergence,
reference-floor log-magnitude error and the declared multi-resolution score.
Explain frame inclusion, polarity/phase sensitivity and missing/degenerate values.
Define harmonic, transient and fricative region measures and selection rules.]

### 3.5 Small experimental modification and aggregation

[Compare medium-window-only diagnostics with the three-resolution method,
holding inputs, codec settings and preprocessing fixed. Explain the evidence
that would demonstrate added diagnostic information. Describe paired aggregation,
variability, measured-rate screening and timing-comparability checks. Do not
assume the modification improves intelligibility or gives a novel metric.]

### 3.6 Tools/techniques learned and completion boundary

[Explain newly learned MATLAB/Python/codec techniques in your own understanding.
List any intended method steps not completed so the reader can distinguish
the full research plan from actual execution.]

## 4. Results

No real speech comparison results currently exist in the repository. The four
passing Python integration tests validate preparation/codec round trips on
synthetic input; they do not answer the speech-quality research question.

### 4.1 Software validation

[Insert actual MATLAB test counts, maximum reconstruction errors, invalid-NOLA
behaviour and example verified output. State software versions and failures.]

### 4.2 Data integrity, actual bitrate and runtime

[Insert per-condition sample/utterance counts, measured versus requested rates,
clipping flags, delay/length checks, timing definitions and availability counts.
Explain meaningful mismatches rather than suppressing them.]

### 4.3 Global and multi-resolution speech results

[Insert paired tables/figures across speakers and utterances: SI-SDR, available
STOI, short/medium/long spectral errors, MR diagnostic and variability. Provide
clear captions, units, sample counts and explanatory text. Missing is not zero.]

### 4.4 Speech-structure case studies and the baseline comparison

[Use the same original/Opus/EnCodec utterance at one bitrate, regional error
figures and harmonic/transient/fricative evidence. Explain what medium-only
analysis misses or captures; report negative/unhelpful findings honestly.]

### 4.5 Quality versus implementation cost

[Compare same-machine, same-scope end-to-end runtime with diagnostic outcomes.
Disclose process/model startup overhead; do not label this as inference-only
speed or use a quoted paper's timing as a directly comparable result.]

## 5. Discussion and conclusion

### 5.1 What the evidence answers

[Answer the single research question to the extent supported: full answer,
partial answer or only a validated tool. Explain observed metric disagreements
and structure-specific effects using STFT/codec theory. Avoid an unsupported
global winner or listening-quality/intelligibility claim.]

### 5.2 Relationship to previous work

[Compare observed findings with primary literature: consistency, contradiction,
extension or inability to compare fairly. Support interpretations with citations.]

### 5.3 What worked, what failed and limitations

[Explain successes and failures. Address dataset coverage, short clips/container
overhead, region selection, alignment, phase sensitivity, absent STOI if relevant,
score weighting/floors, tool versions and runtime overhead. Anticipate criticism
and say how each limitation might be resolved.]

### 5.4 Contribution, conclusion and further work

[Identify the actual analysis/software contribution and the scope of evidence.
Propose a small, justified next experiment. Do not present planned neural Opus
or larger-corpus work as completed.]

## References

[Provide complete, verified citations for work actually read and analysed.
Use one consistent course-appropriate style. The README resource list is a
starting point, not a finished literature review or bibliography.]

## Acknowledgements and contribution statement

[Attribute official Opus/EnCodec implementations, pretrained models, datasets,
borrowed material and assistance. State your actual role and demonstrated
understanding accurately. This project's initial code/documentation were
generated with AI assistance; check the course's permitted-use/disclosure rules
and do not claim unassisted independent authorship.]

## Reproduction appendix

[Final code commit, site/code download, permitted example data, dependencies,
commands, actual test logs, corpus manifests/annotations, hashes, missing-feature
behaviour and link to the real demonstration video. Do not publish passwords,
licence files or private speech recordings.]
