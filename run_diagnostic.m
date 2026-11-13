function summary = run_diagnostic(manifestFile, outputDirectory)
%RUN_DIAGNOSTIC Analyse paired WAVs described by a JSON manifest.
% Example: run_diagnostic('results/codecs/utterance/manifest.json','results/report')
arguments
    manifestFile (1,1) string
    outputDirectory (1,1) string
end
assert(~isfolder(outputDirectory), 'codecdiag:OutputExists', ...
    'Choose a new report directory to preserve previous results.');
manifest = jsondecode(fileread(manifestFile));
base = fileparts(manifestFile);
[x,fs] = audioread(fullfile(base,string(manifest.original)));
assert(fs==24000 && size(x,2)==1 && numel(x)>1 && all(isfinite(x)), ...
    'codecdiag:Source', 'Use finite 24-kHz mono speech, prepared identically for both codecs.');
assert(sum(x.^2)>eps, 'codecdiag:Silence', 'Reference is silent.');
configs = codecdiag.settings(fs);
for k = 1:3
    assert(iscola(configs(k).window,configs(k).length-configs(k).hop,'wola'), ...
        'codecdiag:COLA','Analysis window fails weighted COLA.');
end
mkdir(outputDirectory);
rows = struct([]); regionRows = struct([]);
for condition = 1:numel(manifest.conditions)
    entry = manifest.conditions(condition);
    [y,decodedFs] = audioread(fullfile(base,string(entry.decoded)));
    assert(decodedFs==fs && size(y,2)==1 && all(isfinite(y)), ...
        'codecdiag:Decoded', 'Decoded audio must be finite, mono and 24 kHz.');
    delay = fieldOr(entry,'delay_samples',0);
    validateattributes(delay,{'numeric'},{'scalar','integer','nonnegative'});
    rawLength = numel(y);
    assert(rawLength-delay>=numel(x), 'codecdiag:ShortDecoded', ...
        'Decoded audio is too short after declared delay; do not silently pad.');
    % No gain fitting or automatic local time alignment: preserve codec errors.
    y = y(delay+(1:numel(x)));
    wave = codecdiag.waveform_metrics(x,y);
    stoiScore = NaN; stoiStatus = "unavailable";
    if exist('stoi','file')==2 && license('test','Audio_Toolbox')
        % MathWorks convention is processed signal first, reference second.
        stoiScore = stoi(y,x,fs);
        stoiStatus = "computed";
    end
    duration = numel(x)/fs;
    bytes = NaN;
    if isfield(entry,'encoded') && strlength(string(entry.encoded))>0
        file = dir(fullfile(base,string(entry.encoded)));
        assert(numel(file)==1 && ~file.isdir,'codecdiag:EncodedFile','Missing encoded bitstream.');
        bytes = file.bytes;
    end
    encSeconds = fieldOr(entry,'encode_seconds',NaN);
    decSeconds = fieldOr(entry,'decode_seconds',NaN);
    machine = "not supplied";
    if isfield(manifest,'machine'), machine = string(jsonencode(manifest.machine)); end
    row = struct('Utterance',string(manifest.utterance), ...
        'ReferenceSHA256',string(fieldOr(manifest,'prepared_sha256','not supplied')), ...
        'Machine',machine,'Condition',condition, ...
        'Codec',string(entry.codec),'NominalKbps',entry.nominal_kbps, ...
        'MeasuredKbps',8*bytes/duration/1000, ...
        'NominalRateDeviationFraction',abs(8*bytes/duration/1000-entry.nominal_kbps)/max(entry.nominal_kbps,eps), ...
        'EncodedBytes',bytes, ...
        'DurationSeconds',duration,'EncodeSeconds',encSeconds,'DecodeSeconds',decSeconds, ...
        'RealTimeFactor',(encSeconds+decSeconds)/duration, ...
        'NMSE',wave.nmse,'SISDRdB',wave.siSdrDb,'STOI',stoiScore,'STOIStatus',stoiStatus, ...
        'PeakOriginal',wave.peakOriginal,'PeakDecoded',wave.peakDecoded, ...
        'ClippedOriginalSamples',wave.clippedOriginalSamples, ...
        'ClippedDecodedSamples',wave.clippedDecodedSamples, ...
        'RawDecodedSamples',rawLength,'RemovedDelaySamples',delay, ...
        'TrimmedTailSamples',rawLength-delay-numel(x));
    fig = figure('Visible','off','Position',[50 50 1400 1200]);
    cleanup = onCleanup(@() close(fig));
    tiledlayout(fig,4,3,'TileSpacing','compact');
    scores = zeros(1,3);
    for k = 1:3
        c = configs(k);
        [X,meta] = codecdiag.analyse(x,c);
        Y = codecdiag.analyse(y,c);
        e = codecdiag.spectral_error(X,Y);
        prefix = char(c.name);
        row.([prefix 'LogMagnitudeDb']) = e.logMagnitudeDb;
        row.([prefix 'Convergence']) = e.convergence;
        scores(k) = e.normalised;
        bins = 1:floor(c.nfft/2)+1;
        frequencies = (bins-1)*fs/c.nfft/1000;
        times = ((0:size(X,2)-1)*c.hop+c.length/2-meta.padding)/fs;
        keep = times>=0 & times<=duration;
        A = abs(X(bins,keep)); B = abs(Y(bins,keep));
        scale = max(max(A(:)),eps); floorValue = scale*1e-5;
        panels = {20*log10(max(A,floorValue)/scale), ...
            20*log10(max(B,floorValue)/scale), ...
            20*log10(max(abs(Y(bins,keep)-X(bins,keep)),floorValue)/scale), ...
            20*log10(max(B,floorValue)./max(A,floorValue))};
        labels = ["Original" "Decoded" "Complex error STFT" "Log magnitude difference"];
        for panel = 1:4
            ax = nexttile((panel-1)*3+k);
            imagesc(ax,times(keep),frequencies,panels{panel}); axis(ax,'xy');
            if panel==4, clim(ax,[-40 40]); else, clim(ax,[-100 0]); end
            title(ax,sprintf('%s: %s (%g ms)',labels(panel),c.name,1000*c.length/fs));
            xlabel(ax,'Time (s)'); ylabel(ax,'Frequency (kHz)'); colorbar(ax);
        end
    end
    row.MultiResolutionError = mean(scores);
    rows(condition) = row;
    sgtitle(fig,sprintf('%s | %s | target %g kb/s',manifest.utterance,entry.codec,entry.nominal_kbps), ...
        'Interpreter','none');
    exportgraphics(fig,fullfile(outputDirectory,sprintf('condition_%02d_spectra.png',condition)));
    clear cleanup
    fig = figure('Visible','off','Position',[50 50 1200 600]);
    cleanup = onCleanup(@() close(fig));
    tiledlayout(fig,2,1);
    t = (0:numel(x)-1)/fs;
    nexttile; plot(t,x,t,y); legend('Original','Decoded'); ylabel('Amplitude');
    title(sprintf('%s, %g kb/s; no output normalisation',entry.codec,entry.nominal_kbps));
    nexttile; plot(t,y-x); xlabel('Time (s)'); ylabel('Decoded - original');
    exportgraphics(fig,fullfile(outputDirectory,sprintf('condition_%02d_waveforms.png',condition)));
    clear cleanup
    if isfield(manifest,'regions') && ~isempty(manifest.regions)
        local = codecdiag.region_metrics(x,y,fs,manifest.regions,configs);
        for r = 1:numel(local)
            local(r).Condition = condition;
            local(r).Codec = string(entry.codec);
            local(r).NominalKbps = entry.nominal_kbps;
        end
        regionRows = [regionRows local]; %#ok<AGROW>
    end
end
assert(~isempty(rows),'codecdiag:NoConditions','Manifest has no conditions.');
summary = struct2table(rows);
writetable(summary,fullfile(outputDirectory,'summary.csv'));
if ~isempty(regionRows)
    writetable(struct2table(regionRows),fullfile(outputDirectory,'regions.csv'));
end
provenance = struct('createdUTC',char(datetime('now','TimeZone','UTC')), ...
    'matlabVersion',version,'toolboxes',ver,'manifest',manifest,'settings',configs);
writeText(fullfile(outputDirectory,'provenance.json'),jsonencode(provenance,PrettyPrint=true));
report = ["# Speech Codec Diagnostic Report"; ""; ...
    "Results describe signal differences; they do not establish perceptual superiority."; ...
    "See summary.csv for metrics, regions.csv for annotated speech regions (if supplied),"; ...
    "and provenance.json for settings, versions and the input manifest."; ""; ...
    "Measured bitrate includes the complete encoded container/header, not the WAV."; ...
    "Runtime scope: " + string(fieldOr(manifest,'timing_scope','Not supplied; do not compare runtime.')); ...
    "No independent output gain normalisation or automatic time warping is applied."; ...
    "STOI is NaN/unavailable when the MathWorks stoi function is absent."; ...
    "Spectrograms share the original reference level at each resolution (-100 to 0 dB)."; ...
    "Signed log-magnitude difference panels use -40 to +40 dB."; ""; ...
    "## Conditions"];
for k = 1:height(summary)
    r = summary(k,:);
    report(end+1) = sprintf('- %s %g kb/s: measured %.3f kb/s; NMSE %.4g; SI-SDR %.2f dB; STOI %.4g (%s); MR error %.4g; RTF %.3f; clipped decoded samples %d.', ...
        r.Codec,r.NominalKbps,r.MeasuredKbps,r.NMSE,r.SISDRdB,r.STOI,r.STOIStatus, ...
        r.MultiResolutionError,r.RealTimeFactor,r.ClippedDecodedSamples);
    report(end+1) = sprintf('![Spectra](condition_%02d_spectra.png)',k);
    report(end+1) = sprintf('![Waveforms](condition_%02d_waveforms.png)',k);
end
writeText(fullfile(outputDirectory,'report.md'),strjoin(report,newline));
disp(summary);
end

function value = fieldOr(entry,name,fallback)
if isfield(entry,name), value = entry.(name); else, value = fallback; end
end

function writeText(path,text)
fid = fopen(path,'w'); assert(fid~=-1,'codecdiag:Write','Cannot write report.');
cleanup = onCleanup(@() fclose(fid));
fprintf(fid,'%s\n',text);
end
