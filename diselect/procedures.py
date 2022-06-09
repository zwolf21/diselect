import logging
from itertools import groupby
from collections import deque

from .exceptions import *



logging.basicConfig(format='diselect %(levelname)s: %(message)s')



def normalize_query(query):
    if isinstance(query, dict):
        query = [query]
    qs = {}
    for qry in query:
        if isinstance(qry, dict):
            for q, rest in qry.items():
                if isinstance(q, str):
                    q = q,
                if isinstance(rest, (list, tuple)) and len(rest) == 2:
                    alias, apply = rest
                elif isinstance(rest, str):
                    alias, apply = rest, lambda x:x
                else:
                    raise InvalidQueryValues(rest)
                qs[q] = (alias, apply)
        elif isinstance(qry, (tuple,)):
            qs[qry] = (qry, lambda x:x)
        elif isinstance(qry, str):
            qs[(qry,)] = (qry, lambda x:x)
        else:
            raise InvalidQueryKey(qry)
    return qs


def flatten_container(container):
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


def select_container(norm_query, flatten):
    
    def query_match(path, query):
        if len(query) > len(path):
            return False
        return path[-len(query):] == query

    queries = norm_query.keys()

    matched = {}
    for index, path, value in flatten:
        for query in queries:
            if query_match(path, query):
                if exists := matched.get(query):
                    if exists != path:
                        raise QueryMultipleMatched(query, exists, path)
                matched[query] = path
                yield index, path, query, value,

    if under_matched := (queries - matched.keys()):
        logging.warning(f'Cannot find path of {under_matched}')



def groupby_selected(selected):

    def get_common_index_length(selected):
        if index_lengths := [len(index) for index, *_ in selected]:
            return min(index_lengths)
    
    selected = sorted(selected, key=lambda sel: sel[0])
    
    common_index_length = get_common_index_length(selected)

    for name, grouped in groupby(selected, key=lambda sel: sel[0][:common_index_length]):
        select = {}
        for sel in grouped:
            index, path, query, value = sel
            if len(index) == common_index_length:
                select.update({query: value})
            elif len(index) > common_index_length:
                select.setdefault(query, []).append(value)
        yield select


def transform_selected(norm_query, selected):
    # ordering
    quries = list(norm_query.keys())
    selected = [
        {q:sel[q] for q in quries if q in sel}
        for sel in selected
    ]
    #aliasing
    for select in selected:
        transformed = {}
        for qry, val in select.items():
            alias, apply = norm_query[qry]
            try:
                transformed[alias] = apply(val)
            except Exception as e:
                transformed[alias] = val
                logging.warning(f'apply function {apply} for value has failed due to{e}\nreturn to original value: {val}')
        yield transformed


    