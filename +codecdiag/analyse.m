function [S, meta] = analyse(x, config)
%ANALYSE Full complex STFT with explicit boundary padding for exact inversion.
validateattributes(x, {'double'}, {'vector','real','finite','nonempty'});
L = config.length; H = config.hop; N = config.nfft;
validateattributes(L, {'numeric'}, {'scalar','integer','positive'});
validateattributes(H, {'numeric'}, {'scalar','integer','positive','<=',L});
validateattributes(N, {'numeric'}, {'scalar','integer','positive'});
assert(N>=L,'codecdiag:FFTSize','FFT length must not truncate the analysis window.');
w = config.window(:);
assert(numel(w)==L && all(isfinite(w)), 'codecdiag:Window', 'Invalid window.');
x = x(:);
% One whole window at each boundary avoids the zero endpoints of Hann.
xp = [zeros(L,1); x; zeros(L,1)];
frames = 1 + ceil((numel(xp)-L)/H);
total = (frames-1)*H + L;
xp(end+1:total) = 0;
S = complex(zeros(N,frames));
for frame = 1:frames
    indices = (frame-1)*H + (1:L);
    S(:,frame) = fft(xp(indices).*w,N);
end
meta = struct('samples',numel(x),'padding',L,'paddedSamples',total);
end
