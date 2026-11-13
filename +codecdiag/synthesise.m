function x = synthesise(S, meta, config)
%SYNTHESISE Weighted overlap-add, normalised by the squared-window sum.
L = config.length; H = config.hop; w = config.window(:);
assert(size(S,1)==config.nfft, 'codecdiag:FFTSize', 'FFT size mismatch.');
y = zeros(meta.paddedSamples,1); weight = y;
for frame = 1:size(S,2)
    indices = (frame-1)*H + (1:L);
    segment = real(ifft(S(:,frame),config.nfft));
    y(indices) = y(indices) + segment(1:L).*w;
    weight(indices) = weight(indices) + w.^2;
end
indices = meta.padding + (1:meta.samples);
assert(all(weight(indices)>1e-12), 'codecdiag:NOLA', ...
    'Window/hop leaves uncovered samples: NOLA fails.');
x = y(indices)./weight(indices);
end
