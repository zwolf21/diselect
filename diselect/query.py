from .exceptions import *
from .utils import concat_matrix

from functools import partial




def _serialize_query(query):
    if isinstance(query, dict):
        yield query
    elif isinstance(query, list):
        yield from query
    else:
        raise TypeError("Query must be dict or list not {}".format(type(queries)))


def reversed(query):
    quries = _serialize_query(query)


def _norm_query_key(query):
    if isinstance(query, str):
        return (query,),
    elif isinstance(query, tuple):
        sample, *_ = query
        if isinstance(sample, str):
            return query,
        elif isinstance(sample, tuple):
            return query
    elif isinstance(query, dict):
        return {
            _norm_query_key(k):v for k,v in query.items()
        }
    raise InvalidQueryValues(query)



def _set_query_params(query):
    default_apply = lambda x:x
    qs = {}
    if isinstance(query, (str, tuple)):
        qs[query] = (query, default_apply)
    elif isinstance(query, dict):
        for qry, params in query.items():
            if isinstance(params, str):
                qs[qry] = (params, default_apply)
            elif isinstance(params, (tuple, list)) and len(params) == 2:
                alias, apply = params
                if isinstance(apply, str):
                    apply = partial(concat_matrix, seps=apply)
                qs[qry] = (alias, apply)
            else:
                raise InvalidQueryValues(params)
    return qs


def resolve_query(query):
    queries = _serialize_query(query)
    norm_value_quries = map(_set_query_params, queries)
    norm_key_quries = map(_norm_query_key, norm_value_quries)
    resolved = {k:v for qry in norm_key_quries for k,v in qry.items()}
    return resolved


def query_match(path, query):
    for qry in query:
        if len(qry) > len(path):
            continue
        if path[-len(qry):] == qry:
            return True
    return False


def get_priority(query, path):
    for i, qry in enumerate(query):
        if query_match(path, (qry,)):
            return i
