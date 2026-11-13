function run_real_experiment(corpusDirectory,outputDirectory)
%RUN_REAL_EXPERIMENT One entry point for MATLAB Online verification and reports.
% Default paths are anchored to this file, independent of the current folder.
arguments
    corpusDirectory (1,1) string = ""
    outputDirectory (1,1) string = ""
end
root=string(fileparts(mfilename('fullpath')));
if strlength(corpusDirectory)==0
    dataDirectory=fullfile(root,'experiment_data');
    archive=fullfile(root,'deliverables','matlab_online_data.zip');
    if ~isfolder(dataDirectory) && isfile(archive)
        fprintf('Extracting bundled real speech data to %s\n',dataDirectory);
        unzip(archive,root); % First use only: never overwrite existing data.
    end
    corpusDirectory=fullfile(dataDirectory,'real_codecs');
end
if strlength(outputDirectory)==0
    outputDirectory=fullfile(root,'results','matlab_real');
    if isfolder(outputDirectory)
        stamp=string(datetime('now','Format','yyyyMMdd_HHmmss_SSS'));
        outputDirectory=fullfile(root,'results',"matlab_real_"+stamp);
    end
end
assert(~isfolder(outputDirectory),'codecdiag:OutputExists','Use a new output directory.');
files=dir(fullfile(corpusDirectory,'*','manifest.json'));
assert(numel(files)==12,'codecdiag:Corpus', ...
    'Expected 12 LibriSpeech manifests in %s. Extract the bundled ZIP into the project root.',corpusDirectory);
fprintf('Reports and actual MATLAB log will be saved in %s\n',outputDirectory);
mkdir(outputDirectory);
diary(fullfile(outputDirectory,'matlab_run.log'));
cleanup=onCleanup(@()diary('off'));
fprintf('Actual MATLAB runtime: %s\n',version);
run_project_tests(); % No zero-test success or skipped failures; captured in diary.
validation=validate_stft();
writetable(validation,fullfile(outputDirectory,'stft_validation.csv'));
reportDirectories=strings(1,numel(files));
for k=1:numel(files)
    manifestFile=fullfile(files(k).folder,files(k).name);
    manifest=jsondecode(fileread(manifestFile));
    reportDirectories(k)=fullfile(outputDirectory,string(manifest.utterance));
    run_diagnostic(manifestFile,reportDirectories(k));
end
summarise_reports(reportDirectories,fullfile(outputDirectory,'aggregate'));
fprintf('Actual MATLAB analysis completed for 12 real utterances / 48 codec conditions.\n');
end
