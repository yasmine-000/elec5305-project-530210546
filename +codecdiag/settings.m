function configs = settings(fs)
%SETTINGS Three physical resolutions; zero padding is not extra resolution.
validateattributes(fs, {'numeric'}, {'scalar','integer','positive'});
durations = [12 28 56]; % milliseconds at 24 kHz: 288, 672, 1344 samples
names = ["short" "medium" "long"];
configs = struct([]);
for k = 1:3
    L = 4 * round(fs * durations(k) / 4000);
    configs(k).name = names(k);
    configs(k).length = L;
    configs(k).hop = L / 4;
    configs(k).nfft = 2^nextpow2(L);
    configs(k).window = 0.5 - 0.5*cos(2*pi*(0:L-1)'/L); % periodic Hann
end
end
