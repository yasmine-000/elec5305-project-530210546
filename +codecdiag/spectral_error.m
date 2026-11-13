function metrics = spectral_error(reference, decoded)
%SPECTRAL_ERROR Reference-anchored log magnitude and spectral convergence.
A = abs(reference); B = abs(decoded);
floorValue = max(max(A(:))*1e-5,eps); % fixed reference-relative -100 dB floor
metrics.logMagnitudeDb = mean(abs(20*log10(max(B,floorValue)) - ...
    20*log10(max(A,floorValue))), 'all');
metrics.convergence = norm(B-A,'fro')/max(norm(A,'fro'),eps);
% Equal weights over three scales; diagnostic, NOT a perceptual metric.
metrics.normalised = 0.5*(metrics.logMagnitudeDb/100 + metrics.convergence);
end
