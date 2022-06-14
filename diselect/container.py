import logging
from itertools import groupby
from functools import reduce

from .utils import apply_to_depth
from .exceptions import *



logging.basicConfig(format='diselect %(levelname)s: %(message)s')



class FlatItem:

    def __init__(self, index, path, value, query=None, _matched_pos=0):
        self.index = index
        self.path = path
        self.value = value
        self.query = query
        self._matched_pos = _matched_pos

    def __str__(self):
        kwargs = {
            k:str(v) for k, v in self.__dict__.items()
        }
        return 'INDEX: {index:<15} PATH: {path:<25} VALUE: {value:<20} QUERY: {query}'.format(**kwargs)

    def populate_matched(self, quries):
        for i, query in enumerate(quries):
            if self.path[-len(query):] == query:
                kwargs = {
                    **self.__dict__,
                    '_matched_pos': i,
                    'query': quries
                }
                yield query, FlatItem(**kwargs)



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



def produce_by_query(flatten, queryset):
    matched = {}
    produced = []
    for flat in flatten:
        for quries in queryset:
            for matched_query, matched_flat in flat.populate_matched(quries):
                if seen := matched.get(matched_query):
                    if seen != matched_flat.path:
                        raise QueryMultipleMatched(matched_query, seen, matched_flat.path)
                matched[matched_query] = matched_flat.path
                produced.append(matched_flat)

    quried = set(reduce(lambda cur, acc: cur+acc, queryset, ()))
    
    if undermatched:=quried-matched.keys():
        logging.warning(f'Cannot match path with query: {undermatched}')

    return produced


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
    return min([len(flat.index) for flat in flatten], default=0)



def groupby_depth(flatten, depth, updates=False):
    flatten = sorted(flatten, key=lambda flat: flat.index[:depth])
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



def merge_multi_query(flatten):
    merged = []
    # should be sorted by _matched_pos for mutiple query to decide merging order
    flatten = sorted(flatten, key=lambda flat: (flat.query, flat.index, flat._matched_pos))
    for (qry, idx), grouped in groupby(flatten, key=lambda flat: (flat.query, flat.index)):
        if len(qry) > 1:
            values = []
            paths = ()
            for flat in grouped:
                paths = *paths, flat.path
                values.append(flat.value)
            
            merged.append(FlatItem(idx, paths, values, qry))
        else:
            merged += list(grouped)
    return merged



def _skip_none(none, value, key, row):
    if none == 'ignore' and value is None:
        row[key] = value
        return True
    if none == 'drop' and value is None:
        return True
    if none == 'apply' and value is None:
        return False


def _reduce(app, value, depth=0):
    
    def _join(iterable, sep=app):
        return sep.join(filter(None, iterable))

    function_for_iterable =  [
        sum, min, max, len,
        all, any,
        list, tuple, set,
        _join, 
    ]
    
    if isinstance(app, str):
        app = _join
    elif app.__name__ == 'join':
        function_for_iterable.append(app)

    if app in function_for_iterable:
        depth = 1

    return apply_to_depth(depth, app, value)

# 1
def apply_value(selected, qs, none, **kwargs):
    sel = {}
    for query, value in selected.items():
        _, [*applies] = qs[query]
        
        if _skip_none(none, value, query, sel):
            continue

        for app in applies:
            value = _reduce(app, value)

        sel[query] = value
    return sel

# 2
def alias_fields(selected, qs):
    sel = {}
    for quries, value in selected.items():
        alias, *_ = qs[quries]
        sel[alias] = value
    return sel

# 3
def order_column(aliased, qs):
    fields = [v[0] for k, v in qs.items()]
    return {
        k: aliased[k] for k in fields if k in aliased
    }


def transform_selected(selected, qs, **kwargs):
    applied = map(lambda sel: apply_value(sel, qs, **kwargs), selected)
    aliased = map(lambda sel: alias_fields(sel, qs), applied)
    ordered = map(lambda sel: order_column(sel, qs), aliased)
    yield from ordered