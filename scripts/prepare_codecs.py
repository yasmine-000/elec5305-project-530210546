#!/usr/bin/env python3
"""Prepare one paired utterance and real Opus/EnCodec bitstreams.

FFmpeg is required. EnCodec is optional and runs as a CPU subprocess using
Meta's public bitstream API. All timings include command/model startup and I/O.
"""
from __future__ import annotations

import argparse
from array import array
import ctypes
import ctypes.util
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

RATE = 24000


def command(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, capture_output=True, **kwargs)


def timed(args):
    start = time.perf_counter()
    command(args)
    return time.perf_counter() - start


def read_audio(path):
    """Read float WAV without clipping; standard-library-only inspection."""
    info = json.loads(command(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_entries', 'stream=sample_rate,channels', '-of', 'json', path]).stdout)
    stream = info['streams'][0]
    raw = command(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f64le', '-c:a',
                   'pcm_f64le', '-']).stdout
    samples = array('d')
    samples.frombytes(raw)
    if sys.byteorder != 'little':
        samples.byteswap()
    if not samples or any(not math.isfinite(v) for v in samples):
        raise ValueError(f'Empty or nonfinite audio: {path}')
    channels = int(stream['channels'])
    rate = int(stream['sample_rate'])
    return samples, rate, channels


def audio_stats(path):
    samples, rate, channels = read_audio(path)
    return {'sample_rate': rate, 'channels': channels,
            'samples_per_channel': len(samples) // channels,
            'peak': max(abs(v) for v in samples),
            'samples_at_or_above_full_scale': sum(abs(v) >= 1 for v in samples)}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def opus_commands(original, encoded, decoded, kbps):
    # libopus 1.5.2 initialises decoder complexity to 0. LACE/NoLACE require
    # complexity >=6/7; FFmpeg's wrapper does not raise it. See protocol.md.
    encode = ['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', original,
              '-c:a', 'libopus', '-application', 'voip', '-b:a', f'{kbps}k',
              '-vbr', 'off', '-frame_duration', '20', '-ac', '1', encoded]
    decode = ['ffmpeg', '-nostdin', '-v', 'error', '-n', '-c:a', 'libopus', '-i',
              encoded, '-ar', str(RATE), '-ac', '1', '-c:a', 'pcm_f32le', decoded]
    return encode, decode


def encodec_worker(mode, source, destination, kbps):
    # Dependencies are imported only for the neural condition.
    import torch
    from encodec import EncodecModel
    from encodec.compress import compress, decompress
    torch.set_num_threads(1)
    if mode == '_encodec_encode':
        samples, rate, channels = read_audio(source)
        if rate != RATE or channels != 1:
            raise ValueError('EnCodec input must already be 24-kHz mono.')
        wav = torch.tensor(samples, dtype=torch.float32).unsqueeze(0)
        model = EncodecModel.encodec_model_24khz().cpu().eval()
        model.set_target_bandwidth(float(kbps))
        # No language-model entropy coding: controlled nominal 6/12 kb/s.
        with torch.inference_mode():
            payload = compress(model, wav, use_lm=False)
        Path(destination).write_bytes(payload)
    else:
        with torch.inference_mode():
            wav, rate = decompress(Path(source).read_bytes(), device='cpu')
        if rate != RATE or wav.shape[0] != 1:
            raise ValueError('Unexpected neural decoder format.')
        raw = wav.detach().cpu().to(torch.float32).contiguous().numpy().tobytes()
        # Float WAV preserves overshoots, rather than silently clamping PCM16.
        command(['ffmpeg', '-nostdin', '-v', 'error', '-n', '-f', 'f32le',
                 '-ar', str(rate), '-ac', '1', '-i', '-', '-c:a', 'pcm_f32le',
                 destination], input=raw)


def prepare(source, output, codecs, bitrates, gain_db):
    source = Path(source).resolve()
    output = Path(output).resolve()
    if not source.is_file():
        raise ValueError(f'Input does not exist: {source}')
    for executable in ('ffmpeg', 'ffprobe'):
        if not shutil.which(executable):
            raise RuntimeError(f'{executable} is required.')
    if 'encodec' in codecs:
        for package in ('torch', 'torchaudio', 'encodec'):
            importlib.metadata.version(package)  # Fail before creating output.
    output.mkdir(parents=True, exist_ok=False)
    source_stats = audio_stats(source)
    original = output / 'original.wav'
    prep = ['ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', source, '-vn',
            '-ac', '1', '-ar', str(RATE), '-af', f'volume={gain_db}dB',
            '-c:a', 'pcm_f32le', original]
    command(prep)
    stats = audio_stats(original)
    if stats['samples_at_or_above_full_scale']:
        raise ValueError('Prepared reference clips. Reduce --gain-db and use a new output folder.')
    if stats['peak'] < 1e-8:
        raise ValueError('Reference is silent.')
    duration = stats['samples_per_channel'] / RATE
    manifest = {
        'schema_version': 1, 'utterance': source.stem, 'original': 'original.wav',
        'source_name': source.name, 'source_sha256': sha256(source),
        'prepared_sha256': sha256(original), 'preparation_command': list(map(str, prep)),
        'gain_db': gain_db, 'source_stats': source_stats, 'original_stats': stats,
        'timing_scope': 'CPU subprocess wall time including model/process startup and I/O; no downloads in timed runs',
        'machine': {'platform': platform.platform(), 'host': platform.node(), 'processor': platform.processor(),
                    'logical_cpus': os.cpu_count(), 'python': sys.version},
        'ffmpeg_version': command(['ffmpeg', '-version']).stdout.decode().splitlines()[0],
        'opus_condition': 'libopus encoder/decoder; default decoder complexity (0 in verified libopus 1.5.2); no neural enhancement requested',
        'conditions': [], 'regions': []}
    library = ctypes.util.find_library('opus')
    if library:
        opus = ctypes.CDLL(library)
        opus.opus_get_version_string.restype = ctypes.c_char_p
        manifest['system_libopus_version'] = opus.opus_get_version_string().decode()
    else:
        manifest['system_libopus_version'] = 'unavailable; record FFmpeg linked library manually'
    if 'encodec' in codecs:
        # Prime/check the model cache OUTSIDE timed intervals. No training.
        command([sys.executable, '-c',
                 'from encodec import EncodecModel; EncodecModel.encodec_model_24khz()'])
        manifest['neural_versions'] = {p: importlib.metadata.version(p)
                                       for p in ('torch', 'torchaudio', 'encodec')}
    script = Path(__file__).resolve()
    for codec in codecs:
        for kbps in bitrates:
            stem = f'{codec}_{kbps}k'
            encoded = output / (stem + ('.opus' if codec == 'opus' else '.ecdc'))
            decoded = output / (stem + '.wav')
            if codec == 'opus':
                enc, dec = opus_commands(original, encoded, decoded, kbps)
            else:
                enc = [sys.executable, script, '_encodec_encode', original, encoded, kbps]
                dec = [sys.executable, script, '_encodec_decode', encoded, decoded, kbps]
            enc_seconds = timed(enc)
            dec_seconds = timed(dec)
            decoded_stats = audio_stats(decoded)
            if decoded_stats['sample_rate'] != RATE or decoded_stats['channels'] != 1:
                raise ValueError('Codec output format changed.')
            # Gapless container trimming / official EnCodec length metadata must
            # preserve sample count. Never silently align, pad or fit output gain.
            if decoded_stats['samples_per_channel'] != stats['samples_per_channel']:
                raise ValueError(f'{stem}: decoded length differs; investigate codec delay before analysis.')
            size = encoded.stat().st_size
            manifest['conditions'].append({
                'codec': codec, 'nominal_kbps': kbps, 'encoded': encoded.name,
                'decoded': decoded.name, 'delay_samples': 0,
                'encoded_bytes': size, 'measured_kbps': size*8/duration/1000,
                'nominal_rate_deviation_fraction': abs(size*8/duration/1000-kbps)/kbps,
                'encode_seconds': enc_seconds, 'decode_seconds': dec_seconds,
                'real_time_factor': (enc_seconds+dec_seconds)/duration,
                'decoded_stats': decoded_stats, 'encoded_sha256': sha256(encoded),
                'decoded_sha256': sha256(decoded),
                'encode_command': list(map(str, enc)), 'decode_command': list(map(str, dec))})
            # Keep a valid partial manifest after each completed condition.
            (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
            print(f'{stem}: {size*8/duration/1000:.3f} kb/s, RTF {(enc_seconds+dec_seconds)/duration:.3f}')
    return manifest


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('_encodec_encode', '_encodec_decode'):
        encodec_worker(*sys.argv[1:])
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', required=True, type=Path, help='New output directory; never overwritten')
    parser.add_argument('--codecs', nargs='+', choices=['opus', 'encodec'], default=['opus', 'encodec'])
    parser.add_argument('--bitrates', nargs='+', type=int, choices=[6, 12], default=[6, 12])
    parser.add_argument('--gain-db', type=float, default=-3, help='Common reference gain applied once, before either codec')
    args = parser.parse_args()
    if not math.isfinite(args.gain_db):
        parser.error('--gain-db must be finite')
    try:
        prepare(args.input, args.output, list(dict.fromkeys(args.codecs)),
                list(dict.fromkeys(args.bitrates)), args.gain_db)
    except (ValueError, RuntimeError, FileExistsError, importlib.metadata.PackageNotFoundError,
            subprocess.CalledProcessError) as exc:
        detail = exc.stderr.decode(errors='replace') if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        parser.exit(1, f'Codec preparation failed: {detail}\n')


if __name__ == '__main__':
    main()
