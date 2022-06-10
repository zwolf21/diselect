from collections import deque




def resolve_container(container):
    '''inspect index, path, value
    '''
    initial = (), (0,), container,
    cntrq = deque([initial])
    while cntrq:
        path, index, cntr = cntrq.popleft()
        p = None
        if isinstance(cntr, dict):
            for key, value in cntr.items():
                p = *path, key,
                cntrq.append((p, index, value))
        
        elif isinstance(cntr, (list, tuple, set)):
            for i, c in enumerate(cntr):
                idx = *index, i
                cntrq.append((path, idx, c))
        else:
            yield index, path, cntr,