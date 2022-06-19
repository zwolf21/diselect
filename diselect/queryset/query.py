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

    def path_match(self, path, get_pos=False):
        for i, qry in enumerate(self.queries):
            if path[-len(qry):] == qry:
                return i, qry
    


class MatchedQuery(Query):

    def __init__(self, matched_pos, matched_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matched_pos = matched_pos
        self.matched_path = matched_path



class QuerySet:

    def __init__(self, queryset):
        self.qs = queryset
        self.exact_matchedset = set()
        self.matchedset = {}


    def produce_path_matched(self, path:tuple):
        for query in self.qs:
            if m:= query.path_match(path):
                pos, qry = m
                if path == qry:
                    self.exact_matchedset.add(qry)
                yield MatchedQuery(pos, path, **query.as_kwargs())

    
    def validate_matched(self, matched):
        result = []
        for match in matched:
            if set(match.queries) & self.exact_matchedset:
                if match.path not in match.queries:
                    continue
            
            _, qry = match.path_match(match.path)
            self.matchedset.setdefault(qry, set()).add(match.path)

            result.append(match)
        return result


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

    def raise_for_overmatched(self):
        for qry, paths in self.matchedset.items():
            if len(paths) > 1:
                raise QueryMultipleMatched(qry, paths)

    def filter_undermatched(self):
        return set(self.get_flatten_query()) - self.matchedset.keys()