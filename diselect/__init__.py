from .quries import resolve_query
from .container import *



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
    flatten = flatten_container(container)
    qs = resolve_query(query)
    produced = produce_by_query(flatten, qs)
    pivot_index = get_top_depth(produced)
    selected_groups = groupby_depth(produced, pivot_index)

    for selected in selected_groups:
        selected = merge_multi_query(selected)        
        selected = groupby_depth(selected, pivot_index, updates=True)
        selected = transform_selected(selected, qs, none=none)
        yield from selected
