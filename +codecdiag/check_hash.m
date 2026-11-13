function actual = check_hash(path,entry,field)
%CHECK_HASH Always calculate actual hash and verify metadata when supplied.
actual = codecdiag.hash_file(path);
if isfield(entry,field) && ~isempty(entry.(field))
    expected = string(entry.(field));
    assert(isscalar(expected) && ~isempty(regexp(char(expected),'^[0-9a-fA-F]{64}$','once')), ...
        'codecdiag:HashFormat','Malformed SHA-256 in %s.',field);
    assert(strcmpi(actual,expected),'codecdiag:HashMismatch', ...
        'File hash differs from manifest (%s): %s',field,path);
end
end
