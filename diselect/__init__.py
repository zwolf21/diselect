from .procedures import *
from .query import resolve_query
from .container import resolve_container


def diselect(container, query):
    '''query examples: 
        [field1, field2],
        {
            field1: alias1,
            field2: [alias2, func],
        }
        ex) diselect({('path1,', 'path2): ('alias', int)})
    '''
    norm_query = resolve_query(query)
    records = resolve_container(container)
    selected = select_container(norm_query, records)
    selected = groupby_selected(selected)
    selected = transform_selected(norm_query, selected)
    return selected
