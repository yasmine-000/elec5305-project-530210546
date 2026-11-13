function demonstrate_zero_padding(outputFile)
%DEMONSTRATE_ZERO_PADDING Known synthetic two-tone signal, not research data.
arguments
    outputFile (1,1) string = "results/zero_padding.png"
end
parent = fileparts(outputFile);
if strlength(parent)>0 && ~isfolder(parent), mkdir(parent); end
assert(~isfile(outputFile),'codecdiag:OutputExists','Choose a new output file.');
fs = 24000; configs = codecdiag.settings(fs);
fig = figure('Visible','off','Position',[50 50 1200 400]);
cleanup = onCleanup(@()close(fig)); tiledlayout(fig,1,3);
for k = 1:3
    if k<3, c=configs(1); else, c=configs(3); end
    if k==2, c.nfft=4096; end
    t = (0:c.length-1)'/fs;
    x = sin(2*pi*1000*t)+sin(2*pi*1040*t);
    A = abs(fft(x.*c.window,c.nfft)); bins=1:floor(c.nfft/2)+1;
    nexttile; plot((bins-1)*fs/c.nfft,20*log10(max(A(bins),eps)/max(A)),'-o');
    xlim([700 1300]); ylim([-60 0]); grid on
    xlabel('Frequency (Hz)'); ylabel('Relative magnitude (dB)');
    title(sprintf('%g ms, FFT %d',1000*c.length/fs,c.nfft));
end
sgtitle('Synthetic 1000/1040-Hz tones: zero padding samples the same window spectrum');
exportgraphics(fig,outputFile);
end
