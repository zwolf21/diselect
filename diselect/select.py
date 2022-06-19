import logging
from itertools import groupby

from .utils import apply_to_depth
from .exceptions import *
from .flatten import FlatItem
from .queryset import Query



logging.basicConfig(format='diselect %(levelname)s: %(message)s')



class SelectItem(FlatItem, Query):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def __str__(self):
        return str(self.__dict__)

    def set_mutiple_value_type(self):
        if not isinstance(self.value, (list, tuple)):
            self.value = [self.value]
        
    def merge2multiple_value(self, other):
        self.value.append(other.value)

    def get_matched_parts(self):
        return self.match_path(self.path)

    def get_matched_pos(self):
        matched_parts = self.get_matched_parts()
        return self.queries.index(matched_parts)

    def is_exact_matched(self):
        return self.path in self.queries
    
    def was_exact_matched(self, exact_history):
        return set(self.queries) & set(exact_history)

    

def produce_selected(flatten, queryset):
    selected = [
        SelectItem(**flat.as_kwargs(), **query.as_kwargs())
        for flat in flatten
        for query in queryset.produce_matched(flat.path)
    ]

    exact_matched_history = set([
       sel.get_matched_parts() for sel in selected
       if sel.is_exact_matched()
    ])

    matchedset = {}    
    validated = []
    for item in selected:
        if item.was_exact_matched(exact_matched_history):
            if not item.is_exact_matched():
                continue
        
        parts = item.get_matched_parts()
        matchedset.setdefault(parts, set()).add(item.path)
        validated.append(item)
    
    for parts, paths in matchedset.items():
        if len(paths) > 1:
            raise QueryMultipleMatched(parts, paths)

    if undermatched:=set(queryset.get_flatten_query()) - matchedset.keys():
        logging.warning(f'Cannot match path with query: {undermatched}')

    return validated



def get_top_depth(selected):
    return min([len(sel.index) for sel in selected], default=0)



def produce_rowset(selected, pivot_index):
    groupkey = lambda sel: sel.index[:pivot_index]
    selected = sorted(selected, key=groupkey)
    for index, rowset in groupby(selected, key=groupkey):
        yield rowset
    

def merge_multi_query_rowset(rowset):
    rowset = sorted(rowset, key=lambda sel: (sel.queries, sel.index, sel.get_matched_pos()))
    result = []
    for (queries, index), grouped in groupby(rowset, key=lambda sel: (sel.queries, sel.index)):
        if len(queries) > 1:
            merged, *rest = grouped
            merged.set_mutiple_value_type()
            for sel in rest:
                merged.merge2multiple_value(sel)
            result.append(merged)
        else:
            result += list(grouped)
    return result



def compose_to_values(rowset, pivot_index):
    values = {}
    for sel in rowset:
        key = sel.queries
        value = sel.value
        if len(sel.index) > pivot_index:
            values.setdefault(key, []).append(value)
        else:
            values[key] = value
    return values



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


def apply_value(row, queryset, none):
    result = {}
    for quries, value in row.items():
        
        if _skip_none(none, value, quries, result):
            continue

        query = queryset.get_query(quries)
        
        for app in query.applies:
            value = _reduce(app, value)

        result[quries] = value
    return result


def alias_fields(row, queryset):
    result = {}
    for quries, value in row.items():
        query = queryset.get_query(quries)
        result[query.alias] = value
    return result


def order_column(row, queryset):
    return {
      f:row[f] for f in queryset.get_aliases() if f in row        
    }

