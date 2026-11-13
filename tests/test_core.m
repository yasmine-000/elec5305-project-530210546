function tests = test_core
tests = functiontests(localfunctions);
end

function reconstruction(testCase)
results = validate_stft();
verifyEqual(testCase,height(results),24);
verifyLessThan(testCase,max(results.MaxAbsoluteError),1e-10);
end

function metricsHaveKnownBehaviour(testCase)
t = (0:23999)'/24000;
x = sin(2*pi*300*t);
m = codecdiag.waveform_metrics(x,2*x);
verifyEqual(testCase,m.nmse,1,'AbsTol',1e-12);
verifyTrue(testCase,m.siSdrDb>250);
c = codecdiag.settings(24000);
S = codecdiag.analyse(x,c(1));
e = codecdiag.spectral_error(S,S);
verifyEqual(testCase,[e.logMagnitudeDb,e.convergence,e.normalised],[0 0 0]);
e = codecdiag.spectral_error(S,zeros(size(S)));
verifyEqual(testCase,e.convergence,1,'AbsTol',1e-12);
verifyGreaterThan(testCase,e.normalised,0);
end

function noInvalidFftTruncation(testCase)
c = codecdiag.settings(24000); c = c(1); c.nfft = c.length-1;
verifyError(testCase,@()codecdiag.analyse(ones(1000,1),c), ...
    'codecdiag:FFTSize');
end

function reportsAreGenerated(testCase)
root = tempname;
cleanup = onCleanup(@() rmdir(root,'s'));
summary = demo_project(root);
verifyEqual(testCase,height(summary),1);
verifyTrue(testCase,isnan(summary.MeasuredKbps));
verifyTrue(testCase,isfile(fullfile(root,'report','summary.csv')));
verifyTrue(testCase,isfile(fullfile(root,'report','regions.csv')));
verifyTrue(testCase,isfile(fullfile(root,'report','report.md')));
verifyEqual(testCase,numel(dir(fullfile(root,'report','*.png'))),2);
end
