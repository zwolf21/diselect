import json

from diselect import diselect


def test_sample2():
    with open('./test/sample2.json', encoding='utf-8') as fp:
        records = json.loads(fp.read())

    query = {
        ('items', 'id'): 'review_id',
        ('items', 'rating'): 'rating',
        ('items', 'author', 'id'): 'author_id',
        ('items', 'author', 'nickname'): 'author_nickname',
        ('items', 'votedKeywords', 'code'): 'tags'
    }        

    for row in diselect(records, query):
        print(row)
