function tests = test_core
tests = functiontests(localfunctions);
end

function testReconstruction(testCase)
results = validate_stft();
verifyEqual(testCase,height(results),24);
verifyLessThan(testCase,max(results.MaxAbsoluteError),1e-10);
end

function testMetricsHaveKnownBehaviour(testCase)
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

function testNoInvalidFftTruncation(testCase)
c = codecdiag.settings(24000); c = c(1); c.nfft = c.length-1;
verifyError(testCase,@()codecdiag.analyse(ones(1000,1),c), ...
    'codecdiag:FFTSize');
end

function testReportsAreGenerated(testCase)
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

function testFrameMaskExcludesPadding(testCase)
c = codecdiag.settings(24000); c=c(1);
[S,meta] = codecdiag.analyse(ones(1000,1),c);
keep = codecdiag.frame_mask(meta,c,size(S,2));
centres = (0:size(S,2)-1)*c.hop+c.length/2-meta.padding;
verifyEqual(testCase,keep,centres>=0 & centres<1000);
verifyEqual(testCase,sum(keep),14);
verifyTrue(testCase,any(~keep));
end

function testKnownSha256AndTampering(testCase)
path = tempname;
cleanup = onCleanup(@()delete(path));
fid = fopen(path,'wb'); fwrite(fid,uint8('abc'),'uint8'); fclose(fid);
expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
verifyEqual(testCase,codecdiag.hash_file(path),expected);
entry = struct('hash',expected);
verifyEqual(testCase,codecdiag.check_hash(path,entry,'hash'),expected);
fid = fopen(path,'ab'); fwrite(fid,uint8('x'),'uint8'); fclose(fid);
verifyError(testCase,@()codecdiag.check_hash(path,entry,'hash'),'codecdiag:HashMismatch');
end

function testReportRejectsModifiedAudio(testCase)
root = tempname; mkdir(root);
cleanup = onCleanup(@()rmdir(root,'s'));
path = fullfile(root,'original.wav');
audiowrite(path,0.2*sin(2*pi*300*(0:2399)'/24000),24000);
manifest = struct('utterance','tamper_fixture','original','original.wav', ...
    'conditions',struct('codec','fixture','nominal_kbps',0,'decoded','original.wav', ...
    'decoded_sha256',repmat('0',1,64)));
fid = fopen(fullfile(root,'manifest.json'),'w');
fprintf(fid,'%s',jsonencode(manifest)); fclose(fid);
verifyError(testCase,@()run_diagnostic(string(fullfile(root,'manifest.json')), ...
    string(fullfile(root,'report'))),'codecdiag:HashMismatch');
end

function testScaleAndPhaseMetricsDiffer(testCase)
t = (0:2399)'/24000; x=0.2*sin(2*pi*300*t);
wave = codecdiag.waveform_metrics(x,-x);
verifyEqual(testCase,wave.nmse,4,'AbsTol',1e-12);
verifyTrue(testCase,wave.siSdrDb>250); % SI-SDR permits sign/scale changes.
c=codecdiag.settings(24000);
S=codecdiag.analyse(x,c(1));
spectral=codecdiag.spectral_error(S,-S);
verifyEqual(testCase,spectral.convergence,0,'AbsTol',1e-12);
% Magnitude metrics cannot see polarity. Complex-error plots and NMSE can.
verifyGreaterThan(testCase,norm(-S-S,'fro'),0);
end
