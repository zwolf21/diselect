import logging
from itertools import groupby
from operator import itemgetter
from functools import reduce, partial

from .utils import concat
from .exceptions import *



logging.basicConfig(format='diselect %(levelname)s: %(message)s')



class FlatItem:

    def __init__(self, index, path, value, query=None):
        self.index = index
        self.path = path
        self.value = value
        self.query = query

    def __str__(self):
        kwargs = {
            k:str(v) for k, v in self.__dict__.items()
        }
        return 'INDEX: {index:<15} PATH: {path:<25} VALUE: {value:<20} QUERY: {query}'.format(**kwargs)

    def match_query(self, *queries):
        for query in queries:
            if self.path[-len(query):] == query:
                self.query=queries
                return query
        return False



def flatten_container(container, index=None, path=None):
    index = index or (0,)
    path = path or ()

    if not isinstance(container, (dict, list)):
        yield FlatItem(index, path, container)

    if isinstance(container, dict):
        for key, val in container.items():
            yield from flatten_container(val, index, (*path, key))
    elif isinstance(container, (list, tuple, set)):
        for i, val in enumerate(container):
            yield from flatten_container(val, (*index, i), path)



def filter_query(flatten, *queryset):
    filtered = []
    matched = {}
    for flat in flatten:
        for quries in queryset:
            if match:=flat.match_query(*quries):
                filtered.append(flat)
                matched.setdefault(match, set()).add(flat.path)

    quried = set(reduce(lambda cur, acc: cur+acc, queryset, ()))
    
    if undermatched:=quried-matched.keys():
        logging.warning(f'Cannot find path of {undermatched}')

    if overmatched:={k:v for k,v in matched.items() if len(v)>1}:
        raise QueryMultipleMatched(set(*overmatched.keys()), set(*overmatched.values()))

    return filtered



def filter_container_value(flatten):
    visited = set()
    filtered = []
    for flat in flatten:
        if flat.path in visited:
            continue
        if isinstance(flat.value, (dict, list)):
            visited.add(flat.path)
        filtered.append(flat)
    return filtered



def get_top_depth(flatten):
    return min([len(flat.index) for flat in flatten])



def filter_depth(flatten, depth):
    return [
        flat for flat in flatten
        if len(flat.index) == depth
    ]



def groupby_depth(flatten, depth, updates=False):
    for idx, grouped in groupby(flatten, key=lambda flat: flat.index[:depth]):
        if updates is False:
            yield grouped
        else:
            select = {}
            for flat in grouped:
                if len(flat.index) > depth:
                    select.setdefault(flat.query, []).append(flat.value)
                else:
                    select[flat.query] = flat.value
            yield select



def _get_merge_priority(queries, flat):
    for i, query in enumerate(queries):
        if flat.match_query(query):
            return i
    return 0



def merge_multi_query(flatten):
    merged = []
    for (qry, idx), grouped in groupby(flatten, key=lambda flat: (flat.query, flat.index)):
        if len(qry) > 1:
            values = []
            paths = ()
            for flat in grouped:
                pri = _get_merge_priority(qry, flat)
                values.append({'priority': pri, 'value': flat.value})
                paths = *paths, flat.path
            vals = [v['value'] for v in sorted(values, key=itemgetter('priority'))]
            merged.append(FlatItem(idx, paths, vals, qry))
        else:
            merged += list(grouped)
    return merged



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
            if apply is not None:
                if isinstance(apply, str):
                    apply = partial(concat, seps=apply)
                try:
                    transformed[alias] = apply(val)
                except Exception as e:
                    transformed[alias] = val
                    logging.warning(f'apply function {apply} for value has failed due to{e}\nreturn to original value: {val}')
            else:
                transformed[alias] = val
        yield transformed