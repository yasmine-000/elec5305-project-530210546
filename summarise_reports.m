function aggregate = summarise_reports(reportDirectories,outputDirectory)
%SUMMARISE_REPORTS Paired-utterance means/variability and engineering plots.
arguments
    reportDirectories (1,:) string
    outputDirectory (1,1) string
end
assert(~isfolder(outputDirectory),'codecdiag:OutputExists','Choose a new output directory.');
allRows = table(); allRegions = table();
for directory = reportDirectories
    T = readtable(fullfile(directory,'summary.csv'),TextType='string');
    assert(height(T)==4,'codecdiag:Unpaired','Each report needs Opus and EnCodec at 6 and 12 kb/s.');
    assert(numel(unique(T.Utterance))==1 && numel(unique(T.ReferenceSHA256))==1, ...
        'codecdiag:Unpaired','A report must describe the same source utterance.');
    for codec = ["opus" "encodec"]
        for bitrate = [6 12]
            assert(sum(T.Codec==codec & T.NominalKbps==bitrate)==1, ...
                'codecdiag:Unpaired','Missing or duplicate paired codec condition.');
        end
    end
    assert(~any(ismember(T.Utterance,allRowsName(allRows))), ...
        'codecdiag:Duplicate','An utterance was supplied more than once.');
    allRows = [allRows; T]; %#ok<AGROW>
    regionFile = fullfile(directory,'regions.csv');
    if isfile(regionFile)
        R = readtable(regionFile,TextType='string');
        R.Utterance = repmat(T.Utterance(1),height(R),1);
        allRegions = [allRegions;R]; %#ok<AGROW>
    end
end
assert(~isempty(allRows),'codecdiag:Empty','No reports supplied.');
% Runtime comparisons require identical recorded hardware/runtime environment.
runtimeComparable = numel(unique(allRows.Machine))==1 && all(allRows.Machine~="not supplied");
metrics = ["NMSE" "SISDRdB" "STOI" "shortLogMagnitudeDb" "mediumLogMagnitudeDb" ...
    "longLogMagnitudeDb" "MultiResolutionError" "RealTimeFactor" "MeasuredKbps"];
rows = struct([]); count = 0;
for codec = ["opus" "encodec"]
    for bitrate = [6 12]
        count = count+1;
        selected = allRows(allRows.Codec==codec & allRows.NominalKbps==bitrate,:);
        row = struct('Codec',codec,'NominalKbps',bitrate,'Utterances',height(selected));
        for metric = metrics
            values = selected.(metric);
            row.(metric+"Mean") = mean(values,'omitnan');
            row.(metric+"Std") = std(values,'omitnan');
            row.(metric+"Available") = sum(~isnan(values));
        end
        rows(count) = row;
    end
end
aggregate = struct2table(rows);
mkdir(outputDirectory);
writetable(allRows,fullfile(outputDirectory,'all_conditions.csv'));
writetable(aggregate,fullfile(outputDirectory,'means_and_variability.csv'));
fig = figure('Visible','off','Position',[50 50 1200 400]);
cleanup = onCleanup(@()close(fig)); tiledlayout(fig,1,3);
for k = 1:3
    nexttile; hold on
    name = ["short" "medium" "long"]; name = name(k)+"LogMagnitudeDb";
    for codec = ["opus" "encodec"]
        rows = aggregate(aggregate.Codec==codec,:);
        errorbar(rows.MeasuredKbpsMean,rows.(name+"Mean"),rows.(name+"Std"),'-o',DisplayName=codec);
    end
    xlabel('Measured bitrate incl. container (kb/s)'); ylabel('Log-magnitude error (dB)');
    title(name,Interpreter='none'); legend('Location','best'); grid on
end
exportgraphics(fig,fullfile(outputDirectory,'bitrate_vs_spectral_error.png')); clear cleanup
% Different scales remain separate: no assertion of perceptual metric ranking.
fig = figure('Visible','off','Position',[50 50 1200 750]);
cleanup = onCleanup(@()close(fig)); tiledlayout(fig,2,3);
for metric = ["SISDRdB" "STOI" "shortLogMagnitudeDb" "longLogMagnitudeDb" "MultiResolutionError"]
    nexttile; labels = aggregate.Codec+" "+string(aggregate.NominalKbps);
    bar(categorical(labels),aggregate.(metric+"Mean"));
    title(metric,Interpreter='none'); xtickangle(30); grid on
end
exportgraphics(fig,fullfile(outputDirectory,'metric_comparison.png')); clear cleanup
if runtimeComparable
    fig = figure('Visible','off'); cleanup = onCleanup(@()close(fig)); hold on
    for codec = ["opus" "encodec"]
        rows = aggregate(aggregate.Codec==codec,:);
        plot(rows.RealTimeFactorMean,rows.MultiResolutionErrorMean,'-o',DisplayName=codec);
        text(rows.RealTimeFactorMean,rows.MultiResolutionErrorMean,string(rows.NominalKbps));
    end
    xlabel('End-to-end real-time factor'); ylabel('Multi-resolution diagnostic error');
    legend; grid on
    exportgraphics(fig,fullfile(outputDirectory,'quality_vs_complexity.png')); clear cleanup
end
if ~isempty(allRegions)
    writetable(allRegions,fullfile(outputDirectory,'all_regions.csv'));
    fig = figure('Visible','off'); cleanup = onCleanup(@()close(fig)); hold on
    for codec = ["opus" "encodec"]
        for bitrate = [6 12]
            R = allRegions(allRegions.Codec==codec & allRegions.NominalKbps==bitrate,:);
            harmonic = R.LongLogMagnitudeDb(R.Type=="harmonic");
            transient = R.ShortLogMagnitudeDb(R.Type=="transient");
            if ~isempty(harmonic) && ~isempty(transient)
                plot(mean(harmonic),mean(transient),'o',DisplayName=codec+" "+string(bitrate)+"k");
            end
        end
    end
    xlabel('Harmonic-region long-STFT error (dB)'); ylabel('Transient-region short-STFT error (dB)');
    legend; grid on
    exportgraphics(fig,fullfile(outputDirectory,'harmonic_vs_transient.png')); clear cleanup
end
fid = fopen(fullfile(outputDirectory,'README.txt'),'w'); assert(fid~=-1);
cleanup = onCleanup(@()fclose(fid));
fprintf(fid,'Paired utterances: %d. Error bars are utterance SD, not confidence intervals.\n',height(allRows)/4);
fprintf(fid,'Runtime hardware metadata comparable: %d.\n',runtimeComparable);
fprintf(fid,'STOI missing values are omitted; Available columns show counts.\n');
fprintf(fid,'SI-SDR/STOI higher is better; spectral/NMSE/MR errors lower is better.\n');
fprintf(fid,'Inspect regional errors and plots before drawing conclusions. No perceptual claim is implied.\n');
disp(aggregate);
end

function names = allRowsName(rows)
if isempty(rows), names = strings(0,1); else, names = rows.Utterance; end
end
