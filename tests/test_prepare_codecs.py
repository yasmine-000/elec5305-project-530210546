"""Real FFmpeg integration tests, using synthetic fixtures rather than speech."""
from array import array
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
import wave

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'prepare_codecs.py'
spec = importlib.util.spec_from_file_location('prepare_codecs', SCRIPT)
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg and FFprobe required')
class CodecIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'synthetic input.wav'
        # Stereo 48-kHz, non-frame-aligned duration exercises conversion and
        # Opus pre-skip/tail trimming. Not a real speech-quality experiment.
        frames = []
        for n in range(13782):
            value = int(9000*math.sin(2*math.pi*440*n/48000))
            frames.append(struct.pack('<hh', value, value//2))
        with wave.open(str(self.source), 'wb') as out:
            out.setparams((2,2,48000,0,'NONE','not compressed'))
            out.writeframes(b''.join(frames))

    def test_paired_opus_bitrates_and_manifest(self):
        destination = self.root / 'codecs'
        manifest = codec.prepare(self.source, destination, ['opus'], [6,12], -3)
        saved = json.loads((destination / 'manifest.json').read_text())
        self.assertEqual(saved, manifest)
        self.assertEqual(len(saved['conditions']), 2)
        self.assertEqual(saved['original_stats']['sample_rate'], 24000)
        self.assertEqual(saved['original_stats']['channels'], 1)
        self.assertEqual(saved['original_stats']['samples_per_channel'], 6891)
        self.assertEqual(saved['prepared_sha256'], codec.sha256(destination/'original.wav'))
        for entry in saved['conditions']:
            count = entry['decoded_stats']['samples_per_channel']
            self.assertEqual(count, 6891)
            encoded = destination / entry['encoded']
            self.assertEqual(entry['encoded_bytes'], encoded.stat().st_size)
            self.assertAlmostEqual(entry['measured_kbps'], 8*encoded.stat().st_size/(count/24000)/1000)
            self.assertGreater(entry['encode_seconds'], 0)
            self.assertGreater(entry['decode_seconds'], 0)
            self.assertEqual(entry['delay_samples'], 0)
            self.assertIn('libopus', entry['decode_command'])
            self.assertNotIn('-r', entry['decode_command'])
        self.assertGreater(saved['conditions'][1]['encoded_bytes'],saved['conditions'][0]['encoded_bytes'])
        with self.assertRaises(FileExistsError):
            codec.prepare(self.source,destination,['opus'],[6],-3)
        self.assertEqual(json.loads((destination/'manifest.json').read_text()), saved)

    def test_silence_is_rejected(self):
        silent = self.root / 'silence.wav'
        with wave.open(str(silent),'wb') as out:
            out.setparams((1,2,24000,0,'NONE','not compressed'))
            out.writeframes(bytes(4800))
        with self.assertRaisesRegex(ValueError,'silent'):
            codec.prepare(silent,self.root/'silent-output',['opus'],[6],-3)

    def test_float_overshoots_are_preserved_and_flagged(self):
        samples = array('f',[0.0,1.25,-1.4,0.2]*100)
        if sys.byteorder != 'little':
            samples.byteswap()
        path = self.root/'overshoot.wav'
        codec.command(['ffmpeg','-v','error','-f','f32le','-ar','24000','-ac','1',
                       '-i','-','-c:a','pcm_f32le',path], input=samples.tobytes())
        stats = codec.audio_stats(path)
        self.assertAlmostEqual(stats['peak'],1.4,places=5)
        self.assertEqual(stats['samples_at_or_above_full_scale'],200)


if __name__ == '__main__':
    unittest.main()
