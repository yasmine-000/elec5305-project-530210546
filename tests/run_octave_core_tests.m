function run_octave_core_tests(outputFile, corpusDirectory)
%RUN_OCTAVE_CORE_TESTS Supplemental runtime tests, NOT MATLAB test-suite evidence.
% Uses the exact repository analysis/synthesis functions without table/JVM APIs.
fid=fopen(outputFile,'w'); assert(fid~=-1);
cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'runtime,signal,window_samples,hop_samples,fft_samples,max_absolute_error,wola_deviation\n');
rng(5305);
signals={randn(7913,1),[1;zeros(719,1);-1],0.2*ones(37,1),zeros(997,1)};
names={'random','boundary_impulses','short_constant','silence'};
count=0; worst=0;
for L=[288 672 1344]
    c=configuration(L);
    weights=sum(reshape(c.window.^2,c.hop,[]),2);
    deviation=max(abs(weights-1.5)); assert(deviation<1e-12);
    for N=[c.nfft 2*c.nfft]
        c.nfft=N;
        for k=1:numel(signals)
            err=roundTrip(signals{k},c);
            fprintf(fid,'GNU_Octave,%s,%d,%d,%d,%.17g,%.17g\n',names{k},L,c.hop,N,err,deviation);
            count=count+1; worst=max(worst,err);
        end
    end
end
if nargin>1
    folders=dir(corpusDirectory);
    for k=1:numel(folders)
        if ~folders(k).isdir || folders(k).name(1)=='.', continue; end
        path=fullfile(corpusDirectory,folders(k).name,'original.wav');
        if ~isfile(path),continue;end
        [x,fs]=audioread(path); assert(fs==24000 && size(x,2)==1);
        for L=[288 672 1344]
            c=configuration(L); err=roundTrip(x,c);
            fprintf(fid,'GNU_Octave,%s,%d,%d,%d,%.17g,%.17g\n',folders(k).name,L,c.hop,c.nfft,err,0);
            count=count+1; worst=max(worst,err);
        end
    end
end
c=configuration(288); c.hop=c.length;
[S,m]=codecdiag.analyse(ones(576,1),c); rejected=false;
try
    codecdiag.synthesise(S,m,c);
catch exception
    rejected=strcmp(exception.identifier,'codecdiag:NOLA');
end
assert(rejected,'Invalid NOLA case was not rejected.');
x=sin(2*pi*300*(0:23999)'/24000);
metrics=codecdiag.waveform_metrics(x,2*x);
assert(abs(metrics.nmse-1)<1e-12 && metrics.siSdrDb>250);
S=codecdiag.analyse(x,configuration(288));
metrics=codecdiag.spectral_error(S,S);
assert(metrics.logMagnitudeDb==0 && metrics.convergence==0);
fprintf('GNU Octave %s: %d exact-source reconstruction cases passed; max error %.17g; invalid NOLA rejected; known waveform/spectral metrics passed.\n',version,count,worst);
end

function c=configuration(L)
c=struct('length',L,'hop',L/4,'nfft',2^nextpow2(L), ...
    'window',0.5-0.5*cos(2*pi*(0:L-1)'/L));
end

function err=roundTrip(x,c)
[S,m]=codecdiag.analyse(x,c); y=codecdiag.synthesise(S,m,c);
assert(numel(x)==numel(y)); err=max(abs(x-y)); assert(err<1e-10);
end
