function summary = demo_project(outputRoot)
%DEMO_PROJECT Synthetic fixtures only: this is NOT a speech codec experiment.
arguments
    outputRoot (1,1) string = "results/demo"
end
assert(~isfolder(outputRoot),'codecdiag:OutputExists','Choose a new demo directory.');
mkdir(outputRoot);
rng(5305); fs = 24000; t = (0:fs*2-1)'/fs;
x = zeros(size(t));
voiced = t>=0.1 & t<0.7;
for harmonic = 1:12
    x(voiced) = x(voiced) + 0.12/harmonic*sin(2*pi*harmonic*150*t(voiced));
end
transient = t>=0.9 & t<0.92;
x(transient) = 0.25*randn(sum(transient),1).*exp(-150*(t(transient)-0.9));
fricative = t>=1.2 & t<1.8;
noise = filter([1 -1],1,randn(size(t)));
x(fricative) = 0.035*noise(fricative);
y = filter(ones(8,1)/8,1,x);
audiowrite(fullfile(outputRoot,'original.wav'),x,fs,BitsPerSample=24);
audiowrite(fullfile(outputRoot,'lowpass_fixture.wav'),y,fs,BitsPerSample=24);
manifest = struct('utterance','synthetic_fixture_NOT_speech','original','original.wav', ...
    'conditions',struct('codec','synthetic_lowpass_NOT_codec','nominal_kbps',0, ...
        'decoded','lowpass_fixture.wav','delay_samples',0), ...
    'regions',[struct('type','harmonic','start_seconds',0.15,'end_seconds',0.65), ...
        struct('type','transient','start_seconds',0.88,'end_seconds',0.96), ...
        struct('type','fricative','start_seconds',1.25,'end_seconds',1.75)]);
fid = fopen(fullfile(outputRoot,'manifest.json'),'w');
assert(fid~=-1); cleanup = onCleanup(@() fclose(fid));
fprintf(fid,'%s',jsonencode(manifest,PrettyPrint=true)); clear cleanup
summary = run_diagnostic(fullfile(outputRoot,'manifest.json'),fullfile(outputRoot,'report'));
end
