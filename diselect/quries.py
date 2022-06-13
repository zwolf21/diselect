from .exceptions import *
from .utils import get_nested_depth



def query2dict(query):
    qs = {}
    if isinstance(query, (list, tuple)):
        for qry in query:
            if isinstance(qry, (str, tuple)):
                qs[qry] = qry
            elif isinstance(qry, dict):
                qs.update(qry)
    elif isinstance(query, dict):
        qs.update(query)
    else:
        raise InvalidQueryKey(query)
    return qs




def multiply_querykey(key):
    query_depth = get_nested_depth(key)
    switch = {
        0: lambda x: ((x,),),
        1: lambda x: (x,),
        2: lambda x: x
    }
    if trans:= switch.get(query_depth):
        return trans(key)
    else:
        raise ValueError('Too many tuple nesting:{}'.format(key))


def set_queryvalue(value):
    alias, apply = None, [lambda x:x]
    if isinstance(value, str):
        alias = value
    elif isinstance(value, (tuple, list)):
        alias, *apply = value
    else:
        raise InvalidQueryValues(value)
    return alias, apply


def resolve_query(query, _depth=0):
    if _depth == 0:
        query = query2dict(query)
        return resolve_query(query, _depth=_depth+1)
    elif _depth == 1:
        return {
            multiply_querykey(key): set_queryvalue(value)
            for key, value in query.items()
        }


def get_alias(qs, paths):
    alias, *_ = qs[paths]
    return alias