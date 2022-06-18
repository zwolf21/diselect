from functools import reduce

from ..utils import ParameterBase
from ..exceptions import QueryMultipleMatched



class Query(ParameterBase):

    def __init__(self, queries, alias, applies, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queries = queries
        self.alias = alias
        self.applies = applies

    def __str__(self):
        return 'queries: {queries:<15} alias: {alias:<25}'.format(
            queries=str(self.queries), alias=self.alias
        )


class MatchedQuery(Query):

    def __init__(self, matched_pos, matched_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matched_pos = matched_pos
        self.matched_path = matched_path



class QuerySet:

    def __init__(self, queryset):
        self.qs = queryset

    def produce_path_matched(self, path:tuple, matchedset:dict):
        for query in self.qs:
            for p, qry in enumerate(query.queries):
                if path[-len(qry):] == qry:
                    matchedset.setdefault(qry, set()).add(path)
                    yield MatchedQuery(p, path, **query.__dict__)
    
    def get_query(self, queries):
        for query in self.qs:
            if query.queries == queries:
                return query

    def get_flatten_query(self):
        return reduce(lambda acc, cur: acc + cur.queries, self.qs, ())

    def get_aliases(self):
        return [
            q.alias for q in self.qs
        ]

    def raise_for_overmatched(self, matchedset):
        for qry, paths in matchedset.items():
            if len(paths) > 1:
                raise QueryMultipleMatched(qry, paths)

    def filter_undermatched(self, matchedset):
        return set(self.get_flatten_query()) - matchedset.keys()