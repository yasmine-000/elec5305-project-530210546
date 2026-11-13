"""Opt-in official pretrained EnCodec/Opus round trips; synthetic data only."""
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import tempfile
import unittest
import wave

SCRIPT = Path(__file__).resolve().parents[1]/'scripts'/'prepare_codecs.py'
spec = importlib.util.spec_from_file_location('prepare_neural',SCRIPT)
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)


@unittest.skipUnless(os.environ.get('CODECDIAG_TEST_NEURAL')=='1',
                     'Set CODECDIAG_TEST_NEURAL=1 with neural dependencies/model access')
class NeuralIntegrationTests(unittest.TestCase):
    def test_four_real_bitstream_round_trips(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'synthetic.wav'; samples=8407
            with wave.open(str(source),'wb') as out:
                out.setparams((1,2,24000,0,'NONE','not compressed'))
                out.writeframes(b''.join(struct.pack('<h',int(6000*math.sin(2*math.pi*200*n/24000)))
                                         for n in range(samples)))
            output=root/'conditions'
            manifest=codec.prepare(source,output,['opus','encodec'],[6,12],-3)
            self.assertEqual(len(manifest['conditions']),4)
            self.assertEqual(json.loads((output/'manifest.json').read_text()),manifest)
            for entry in manifest['conditions']:
                self.assertEqual(entry['decoded_stats']['samples_per_channel'],samples)
                self.assertGreater(entry['decoded_stats']['peak'],0)
                self.assertEqual(entry['decoded_sha256'],codec.sha256(output/entry['decoded']))
                self.assertEqual(entry['encoded_sha256'],codec.sha256(output/entry['encoded']))
                self.assertGreater(entry['encoded_bytes'],0)
                self.assertGreater(entry['real_time_factor'],0)
            self.assertEqual(manifest['neural_versions']['encodec'],'0.1.1')


if __name__=='__main__':
    unittest.main()
