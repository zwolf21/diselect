import logging
from itertools import groupby

from .utils import apply_to_depth, ParameterBase
from .exceptions import *
from .flatten import FlatItem
from .queryset import MatchedQuery



logging.basicConfig(format='diselect %(levelname)s: %(message)s')



class SelectItem(FlatItem, MatchedQuery):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def __str__(self):
        return str(self.__dict__)

    def set_mutiple_value_type(self):
        if not isinstance(self.value, (list, tuple)):
            self.value = [self.value]
        
    def merge2multiple_value(self, other):
        self.value.append(other.value)




def produce_selected(flatten, queryset):
    validator = {}
    result = [
        SelectItem(**flat.as_kwargs(), **matched.as_kwargs())
        for flat in flatten
        for matched in queryset.produce_path_matched(flat.path, validator)
    ]

    queryset.raise_for_overmatched(validator)

    if undermatched := queryset.filter_undermatched(validator):
        logging.warning(f'Cannot match path with query: {undermatched}')
 
    return result


def get_top_depth(selected):
    return min([len(sel.index) for sel in selected], default=0)


def produce_rowset(selected, pivot_index):
    groupkey = lambda sel: sel.index[:pivot_index]
    selected = sorted(selected, key=groupkey)
    for index, rowset in groupby(selected, key=groupkey):
        yield rowset
    

def merge_multi_query_rowset(rowset):
    rowset = sorted(rowset, key=lambda sel: (sel.queries, sel.index, sel.matched_pos))
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

