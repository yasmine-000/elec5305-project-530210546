# Clean speech data

Do not commit private recordings or an entire speech corpus. Start with 10–20
clean utterances from several LibriSpeech speakers, or speech you have permission
to use. Dataset entry point: https://www.openslr.org/12/ (check corpus terms).

For each recording keep a local table containing: utterance ID, speaker ID,
corpus/split, source URL or recording consent, original sample rate, transcript,
duration, selected regions and any exclusions. Avoid choosing only examples
that make one codec look good. Separate development/debug examples from the
final selected subset.

Place a WAV under this ignored data folder and run `scripts/prepare_codecs.py`
from the repository root. It produces one shared 24-kHz mono float reference
with a common -3 dB gain before both codecs. Keep source audio unchanged.
Never normalise each decoded output independently.

Manually inspect the clean recording and annotate stable voiced vowels,
isolated plosive/onset transients, and fricatives. Use seconds and the types
`harmonic`, `transient`, `fricative` in `manifest.json`. Use the same annotations
for both codecs and both bitrates. Stable regions should be long enough to
support a 56-ms window; avoid treating a few milliseconds as harmonic evidence.

Record clipping/overshoot flags, but do not automatically remove a difficult
codec result. Inspect large nominal/measured bitrate differences on short files.
Use sufficiently long speech for meaningful runtime comparisons. A separate
attributed 12-utterance LibriSpeech subset and its codec outputs are now bundled
in `deliverables/matlab_online_data.zip`; see `experiments/real_speech` for actual
selection and results. Source audio is 16 kHz and is resampled once to 24 kHz;
the 8–12-kHz band does not contain original source speech information.
The bundled automatic regions are explicitly acoustic proxies, not verified
phonetic labels. The synthetic demo remains separate from real speech results.
