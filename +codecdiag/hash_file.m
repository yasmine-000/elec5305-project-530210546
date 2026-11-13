function hash = hash_file(path)
%HASH_FILE Streaming SHA-256 over the exact file bytes (MATLAB JVM required).
assert(usejava('jvm'),'codecdiag:JVM','SHA-256 verification requires MATLAB JVM.');
fid = fopen(path,'rb'); assert(fid~=-1,'codecdiag:Read','Cannot read input file.');
cleanup = onCleanup(@()fclose(fid));
digest = java.security.MessageDigest.getInstance('SHA-256');
while ~feof(fid)
    chunk = fread(fid,1024*1024,'*int8');
    if ~isempty(chunk), digest.update(chunk); end
end
[message,number] = ferror(fid);
assert(number==0,'codecdiag:Read','File read failed: %s',message);
bytes = typecast(digest.digest(),'uint8');
hash = string(lower(reshape(dec2hex(bytes,2).',1,[])));
end
