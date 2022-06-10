import logging
from itertools import groupby

from .query import query_match, get_priority
from .exceptions import *



logging.basicConfig(format='diselect %(levelname)s: %(message)s')





def select_container(norm_query, flatten):
    queries = norm_query.keys()

    matched = {}
    for index, path, value in flatten:
        for query in queries:
            if query_match(path, query):
                if exists := matched.get(query):
                    if path not in exists and len(exists) >= len(query):
                        raise QueryMultipleMatched(query, exists, path)
                matched.setdefault(query, set()).add(path)

                yield index, path, query, value,

    if under_matched := (queries - matched.keys()):
        logging.warning(f'Cannot find path of {under_matched}')



def groupby_selected(selected):

    def get_common_index_length(selected):
        if index_lengths := [len(index) for index, *_ in selected]:
            return min(index_lengths)
    
    selected = sorted(selected, key=lambda sel: (sel[0], get_priority(sel[2], sel[1])))
    
    common_index_length = get_common_index_length(selected)

    for _, grouped in groupby(selected, key=lambda sel: sel[0][:common_index_length]):
        grouped = list(grouped)
        select = {}
        for query_group, query_grouped in groupby(grouped, key=lambda sel:(sel[0], sel[2])):
            query_grouped = list(query_grouped)
            # print(query_grouped)
            values = {}
            for (index, path, query, value) in query_grouped:
                values.setdefault(query, []).append(value)
            
            for (index, path, query, value) in grouped:
                if len(index) == common_index_length:
                    if len(query) > 1:
                        if val:=values.get(query):
                            select[query] = val
                    else:
                        select[query] = value
                elif len(index) > common_index_length:
                    if len(query) > 1:
                        if val:= values.get(query):
                            select.setdefault(query, []).append(val)
                            break
                    else:
                        select.setdefault(query, []).append(value)

        yield select


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
            try:
                transformed[alias] = apply(val)
            except Exception as e:
                transformed[alias] = val
                logging.warning(f'apply function {apply} for value has failed due to{e}\nreturn to original value: {val}')
                raise
        yield transformed


    