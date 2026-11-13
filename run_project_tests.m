function results = run_project_tests()
%RUN_PROJECT_TESTS Fail if MATLAB silently discovers no/too few tests.
root = fileparts(mfilename('fullpath'));
suite = testsuite(fullfile(root,'tests','test_core.m'));
assert(numel(suite)>=8,'codecdiag:TestDiscovery', ...
    'Expected at least 8 MATLAB tests; discovered %d.',numel(suite));
results = run(suite);
assert(all([results.Passed]),'codecdiag:TestFailure', ...
    'All MATLAB tests must pass; skipped/incomplete tests are not validation.');
end
