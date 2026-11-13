"""Opt-in numerical cross-checks against independent SciPy conventions."""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

RUN=os.environ.get('CODECDIAG_TEST_ANALYSIS')=='1'
if RUN:
    import numpy as np
    from scipy import signal
    from pystoi import stoi
    path=Path(__file__).resolve().parents[1]/'scripts'/'analyse_corpus.py'
    spec=importlib.util.spec_from_file_location('analyse_corpus',path)
    analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)


@unittest.skipUnless(RUN,'Set CODECDIAG_TEST_ANALYSIS=1 with analysis dependencies')
class AnalysisTests(unittest.TestCase):
    def test_fft_and_frame_times_match_scipy(self):
        x=np.random.default_rng(5305).normal(size=7913)
        for config in analysis.CONFIGS:
            _,length,hop,nfft=config
            actual,times=analysis.stft(x,config)
            window=signal.windows.hann(length,sym=False)
            _,reference_times,reference=signal.stft(x,fs=24000,window=window,
                nperseg=length,noverlap=length-hop,nfft=nfft,boundary='zeros',padded=True,
                return_onesided=False,scaling='spectrum')
            keep=(reference_times>=0)&(reference_times<len(x)/24000)
            np.testing.assert_allclose(times,reference_times[keep],atol=1e-14)
            np.testing.assert_allclose(actual/window.sum(),reference[:,keep],atol=1e-12)

    def test_waveform_metrics_have_analytic_values(self):
        t=np.arange(24000)/24000;x=np.sin(2*np.pi*300*t)
        nmse,sdr=analysis.waveform_metrics(x,2*x)
        self.assertAlmostEqual(nmse,1,places=12);self.assertGreater(sdr,250)
        y=x+0.1*np.cos(2*np.pi*900*t)
        nmse,sdr=analysis.waveform_metrics(x,y)
        self.assertAlmostEqual(nmse,0.01,places=10);self.assertAlmostEqual(sdr,20,places=8)

    def test_spectral_gain_has_known_error(self):
        x=np.ones((17,23),dtype=complex)
        db,convergence,normalised=analysis.spectral_error(x,2*x)
        self.assertAlmostEqual(db,20*np.log10(2),places=12)
        self.assertAlmostEqual(convergence,1,places=12)
        self.assertAlmostEqual(normalised,0.5*(db/100+1),places=12)

    def test_hash_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture';path.write_bytes(b'abc')
            expected=hashlib.sha256(b'abc').hexdigest();analysis.assert_hash(path,expected)
            path.write_bytes(b'abcd')
            with self.assertRaises(ValueError):analysis.assert_hash(path,expected)

    def test_stoi_identity(self):
        x=np.random.default_rng(5305).normal(size=48000)*0.1
        self.assertAlmostEqual(stoi(x,x,24000,extended=False),1,places=10)


if __name__=='__main__':unittest.main()
