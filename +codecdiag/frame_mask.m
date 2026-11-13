function keep = frame_mask(meta,config,frameCount)
%FRAME_MASK Score frame centres inside actual audio, not padding-only frames.
centres = (0:frameCount-1)*config.hop + config.length/2 - meta.padding;
keep = centres>=0 & centres<meta.samples;
assert(any(keep),'codecdiag:Frames','No frame centres fall inside the signal.');
end
