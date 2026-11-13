function rows = region_metrics(x,y,fs,regions,configs)
%REGION_METRICS Manual, reference-selected regions; no codec-dependent selection.
rows = struct([]);
for k = 1:numel(regions)
    r = regions(k);
    assert(any(strcmp(r.type,{'harmonic','transient','fricative'})), ...
        'codecdiag:RegionType','Use harmonic, transient or fricative.');
    assert(r.start_seconds>=0 && r.end_seconds>r.start_seconds && ...
        r.end_seconds<=numel(x)/fs, 'codecdiag:RegionBounds','Region outside reference.');
    indices = floor(r.start_seconds*fs)+1:ceil(r.end_seconds*fs);
    a = x(indices); b = y(indices);
    wave = codecdiag.waveform_metrics(a,b);
    short = localSpectralError(a,b,configs(1));
    long = localSpectralError(a,b,configs(3));
    [~,pa] = max(abs(a)); [~,pb] = max(abs(b));
    [A,meta] = codecdiag.analyse(a,configs(2)); B = codecdiag.analyse(b,configs(2));
    keep = codecdiag.frame_mask(meta,configs(2),size(A,2));
    A = A(:,keep); B = B(:,keep);
    bins = (0:floor(configs(2).nfft/2))';
    band = bins*fs/configs(2).nfft >= 4000;
    A = A(bins+1,:); B = B(bins+1,:);
    % Absolute band-energy ratio, so genuine gain differences remain visible.
    highBandDb = 10*log10(max(sum(abs(B(band,:)).^2,'all'),eps)/ ...
        max(sum(abs(A(band,:)).^2,'all'),eps));
    energyDb = 10*log10(max(sum(b.^2),eps)/max(sum(a.^2),eps));
    rows(k) = struct('Type',string(r.type),'StartSeconds',r.start_seconds, ...
        'EndSeconds',r.end_seconds,'NMSE',wave.nmse, ...
        'ShortLogMagnitudeDb',short.logMagnitudeDb,'LongLogMagnitudeDb',long.logMagnitudeDb, ...
        'PeakTimeDifferenceMs',1000*(pb-pa)/fs, ...
        'EnergyRatioDb',energyDb,'Above4kHzEnergyRatioDb',highBandDb);
end
end

function metrics = localSpectralError(x,y,config)
[X,meta] = codecdiag.analyse(x,config); Y = codecdiag.analyse(y,config);
keep = codecdiag.frame_mask(meta,config,size(X,2));
metrics = codecdiag.spectral_error(X(:,keep),Y(:,keep));
end
