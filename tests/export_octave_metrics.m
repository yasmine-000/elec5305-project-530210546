function export_octave_metrics(corpusDirectory,outputFile)
%EXPORT_OCTAVE_METRICS Execute exact .m metric/STFT functions on real codec WAVs.
% Supplemental Octave execution; does not exercise MATLAB table/plot/STOI APIs.
fid=fopen(outputFile,'w');assert(fid~=-1);cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'utterance,codec,nominal_kbps,nmse,si_sdr_db,short_log_db,short_convergence,medium_log_db,medium_convergence,long_log_db,long_convergence,mr_error\n');
folders=dir(corpusDirectory); count=0;
for k=1:numel(folders)
    if ~folders(k).isdir || folders(k).name(1)=='.',continue;end
    base=fullfile(corpusDirectory,folders(k).name);
    manifestFile=fullfile(base,'manifest.json');if ~isfile(manifestFile),continue;end
    manifest=jsondecode(fileread(manifestFile));
    [x,fs]=audioread(fullfile(base,manifest.original));assert(fs==24000);
    assert(numel(manifest.conditions)==4,'Incomplete codec conditions.');
    for j=1:numel(manifest.conditions)
        entry=manifest.conditions(j);[y,fy]=audioread(fullfile(base,entry.decoded));assert(fy==fs);
        wave=codecdiag.waveform_metrics(x,y); errors=zeros(1,6); scores=zeros(1,3);index=0;
        for L=[288 672 1344]
            c=struct('length',L,'hop',L/4,'nfft',2^nextpow2(L), ...
                'window',0.5-0.5*cos(2*pi*(0:L-1)'/L));
            [X,meta]=codecdiag.analyse(x,c);Y=codecdiag.analyse(y,c);
            keep=codecdiag.frame_mask(meta,c,size(X,2));
            e=codecdiag.spectral_error(X(:,keep),Y(:,keep));
            errors(index+1:index+2)=[e.logMagnitudeDb e.convergence];
            scores(index/2+1)=e.normalised;index=index+2;
        end
        fprintf(fid,'%s,%s,%g',manifest.utterance,entry.codec,entry.nominal_kbps);
        fprintf(fid,',%.17g',[wave.nmse wave.siSdrDb errors mean(scores)]);fprintf(fid,'\n');count=count+1;
    end
end
assert(count==48,'Expected 48 real-speech conditions.');
fprintf('Executed exact repository .m STFT/metric functions under GNU Octave %s for %d real-speech conditions.\n',version,count);
end
