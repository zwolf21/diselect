from .exceptions import *




def norm_query(query):
    if isinstance(query, dict):
        query = [query]
    qs = {}
    for qry in query:
        if isinstance(qry, dict):
            for q, rest in qry.items():
                if isinstance(q, str):
                    q = (q,),
                elif isinstance(q, (tuple, list)):
                    if all(map(lambda e: isinstance(e, str), q)):
                        q = q,
                    else:
                        q = tuple(((x,) if isinstance(x, str) else x for x in q))
                if isinstance(rest, (list, tuple)) and len(rest) == 2:
                    alias, apply = rest
                elif isinstance(rest, str):
                    alias, apply = rest, None
                else:
                    raise InvalidQueryValues(rest)
                qs[q] = (alias, apply)
        elif isinstance(qry, (tuple,)):
            qs[(qry,)] = (qry, None)
        elif isinstance(qry, str):
            qs[((qry,),)] = (qry, None)
        else:
            raise InvalidQueryKey(qry)
    return qs


    