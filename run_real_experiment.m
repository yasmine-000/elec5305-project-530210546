function run_real_experiment(corpusDirectory,outputDirectory)
%RUN_REAL_EXPERIMENT One entry point for MATLAB Online verification and reports.
% Upload/extract the experiment data beside this repository first.
arguments
    corpusDirectory (1,1) string = "experiment_data/real_codecs"
    outputDirectory (1,1) string = "results/matlab_real"
end
assert(~isfolder(outputDirectory),'codecdiag:OutputExists','Use a new output directory.');
files=dir(fullfile(corpusDirectory,'*','manifest.json'));
assert(numel(files)==12,'codecdiag:Corpus','Expected 12 LibriSpeech manifests; check the extracted data path.');
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
