function results = validate_stft()
%VALIDATE_STFT Experiment 0. No speech data or codec is needed.
rng(5305); fs = 24000;
signals = {randn(7913,1), [1;zeros(719,1);-1], 0.2*ones(37,1), zeros(997,1)};
configs = codecdiag.settings(fs);
rows = struct([]); index = 0;
for k = 1:numel(configs)
    c = configs(k);
    % MATLAB Signal Processing Toolbox: weighted overlap-add uses w.^2.
    assert(iscola(c.window,c.length-c.hop,'wola'), ...
        'codecdiag:COLA', 'Selected configuration fails weighted COLA.');
    for nfft = [c.nfft 2*c.nfft]
        c.nfft = nfft;
        for signal = 1:numel(signals)
            x = signals{signal};
            [S,m] = codecdiag.analyse(x,c);
            y = codecdiag.synthesise(S,m,c);
            err = max(abs(x-y));
            assert(numel(x)==numel(y) && err<1e-10, ...
                'codecdiag:Reconstruction', 'STFT reconstruction failed.');
            index = index+1;
            rows(index) = struct('Resolution',c.name,'FFTLength',nfft, ...
                'Signal',signal,'MaxAbsoluteError',err);
        end
    end
end
% A non-overlapping Hann window cannot cover every input sample.
c = configs(1); c.hop = c.length;
[S,m] = codecdiag.analyse(ones(2*c.length,1),c);
try
    codecdiag.synthesise(S,m,c);
    error('codecdiag:TestFailed','Invalid NOLA configuration was accepted.');
catch exception
    assert(strcmp(exception.identifier,'codecdiag:NOLA'));
end
results = struct2table(rows);
disp(results);
fprintf('Experiment 0 passed: %d reconstruction cases and invalid-NOLA rejection.\n',height(results));
end
