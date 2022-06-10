def concat_matrix(lists, seps, _depth=0):
    r = []
    if seps == '':
        sep = ''
    else:
        idx = min(_depth, len(seps)-1)
        sep = seps[idx]
    
    if all(map(lambda x: isinstance(x, list), lists)):
        for l in lists:
            s = concat_matrix(l, seps, _depth=_depth+1)
            r.append(s)
    else:
        return sep.join(map(str, lists))
    return sep.join(map(str, r))