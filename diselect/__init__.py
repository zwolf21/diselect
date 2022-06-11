from .exceptions import *
from .quries import norm_query
from .container import *






def diselect(container, query):
    flatten = flatten_container(container)
    qs = norm_query(query)
    filtered = filter_query(flatten, *qs)
    pivot_index = get_top_depth(filtered)
    selected_groups = groupby_depth(filtered, pivot_index)

    for selected in selected_groups:
        selected = merge_multi_query(selected)        
        selected = groupby_depth(selected, pivot_index, updates=True)
        selected = transform_selected(qs, selected)
        yield from selected
