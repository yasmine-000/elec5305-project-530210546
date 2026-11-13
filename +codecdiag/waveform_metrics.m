function metrics = waveform_metrics(x,y)
%WAVEFORM_METRICS Scale-sensitive NMSE plus scale-invariant SDR.
x = x(:); y = y(:);
assert(numel(x)==numel(y), 'codecdiag:Length', 'Waveform lengths differ.');
metrics.nmse = sum((y-x).^2)/max(sum(x.^2),eps);
xc = x-mean(x); yc = y-mean(y);
target = (dot(yc,xc)/max(dot(xc,xc),eps))*xc;
residual = yc-target;
if sum(target.^2)==0
    metrics.siSdrDb = -Inf;
elseif sum(residual.^2)==0
    metrics.siSdrDb = Inf;
else
    metrics.siSdrDb = 10*log10(sum(target.^2)/sum(residual.^2));
end
metrics.peakOriginal = max(abs(x));
metrics.peakDecoded = max(abs(y));
metrics.clippedOriginalSamples = sum(abs(x)>=1);
metrics.clippedDecodedSamples = sum(abs(y)>=1);
end
