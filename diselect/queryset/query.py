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


    def match_path(self, path):
        for parts in self.queries:
            if path[-len(parts):] == parts:
                return parts
    

        

class QuerySet:

    def __init__(self, queryset):
        self.qs = queryset
        self.exact_matchedset = set()
        self.matchedset = {}


    def produce_matched(self, path:tuple):
        for query in self.qs:
            if matched_parts:= query.match_path(path):
                if path == matched_parts:
                    self.exact_matchedset.add(matched_parts)
                yield Query(**query.as_kwargs())


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
