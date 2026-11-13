# Real experiment data for MATLAB Online

Download `matlab_online_data.zip` (53,168,437 bytes, about 53 MB decimal). It
contains real LibriSpeech reference/decoded WAVs, actual `.opus`/`.ecdc` files,
manifests, the 24 extra Opus rate-matching control outputs, selected raw FLACs,
selection metadata and attribution. It does **not** contain pretrained weights
or the 338-MB original corpus archive.

SHA-256:

```text
a1e34b8613b0a96d31a95204b1cdff431bd7a93f4815f36b8f91c136ea06535f
```

1. Download/extract this GitHub repository and upload it to MATLAB Drive.
2. Set its root as the current folder in MATLAB Online (R2025a if available).
3. Run:

```matlab
unzip('deliverables/matlab_online_data.zip', '.')
run_real_experiment
```

Unzipping creates `experiment_data/real_codecs`, `selected_speech` and
`rate_matched_opus`, with a common attribution file. No Python, FFmpeg, model
download or codec installation is needed for the MATLAB analysis of these WAVs.

`run_real_experiment` requires MATLAB with its JVM and Signal Processing Toolbox.
Audio Toolbox STOI is optional and explicitly marked unavailable if absent.
It runs the eight MATLAB tests, STFT validation, 12 per-utterance reports and
the primary 48-condition aggregation. Results go to `results/matlab_real`;
the actual MATLAB run is recorded in `matlab_run.log`. Do not overwrite prior
reports. For another run use, for example:

```matlab
run_real_experiment('experiment_data/real_codecs','results/matlab_real_2')
```

If MATLAB fails, retain the exact message/log. The existing Python and Octave
results remain separately recorded; they must not be labelled MATLAB results.

Simplified startup is now supported: run only `run_real_experiment`. The default
data/output paths are anchored to the `.m` file's project folder, and a missing
`experiment_data` directory is populated automatically from the bundled ZIP.
Existing data is not overwritten automatically. Repeating a default run creates
a timestamped output folder; explicitly supplied existing output paths are still
rejected. These native MATLAB entry-point changes are statically reviewed, not
claimed to have executed under MATLAB.
Supplemental controls are available as WAVs/CSVs and were analysed in Python;
the default MATLAB entry point deliberately reports only the four core
conditions per utterance.

The audio is adapted from LibriSpeech (c) 2014 by Vassil Panayotov under CC BY 4.0.
Exact source IDs, licence and modifications are included. Do not replace this
notice with a claim of having recorded the speech yourself.
