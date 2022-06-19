import logging

from .select import *
from .queryset import get_queryset
from .flatten import flatten_container



logging.basicConfig(format='diselect %(levelname)s: %(message)s')



def diselect(container, query, none='ignore'):
    ''' - query examples: 
        [field1, field2],
        {
            field1: alias1,
            field2: [alias2, function1, function2, ...],
            field3: [alias2, ','], # join sep
        }
        - useage:
          diselect(data, {('path1,', 'path2): ('alias', int)})
        - parameters
        none -'ignore'(defalut): function appling is ignored for None value
             -'drop': remove column if value is None 
             -'apply': Treated like any other value
    '''
    # prepare data
    flatten = flatten_container(container)
    qs = get_queryset(query)

    # filter data
    matched = produce_selected(flatten, qs)
    selected = qs.validate_matched(matched)
    qs.raise_for_overmatched()
    if undermatched := qs.filter_undermatched():
        logging.warning(f'Cannot match path with query: {undermatched}')

    # grouping and transform data
    pivot_index = get_top_depth(selected)
    for rowset in produce_rowset(selected, pivot_index):
        rowset = merge_multi_query_rowset(rowset)
        values = compose_to_values(rowset, pivot_index)
        values = apply_value(values, qs, none=none)
        values = alias_fields(values, qs)
        yield order_column(values, qs)
