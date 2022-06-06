import json

from diselect import diselect


def test_sample1():
    with open('./test/sample1.json') as fp:
        records = json.loads(fp.read())

    query = [
        'companyName',
        'website',
        {
            'email':('email', lambda e: e.split('@')),
            ('nested', 'representedBrands'): ('representedBrands', ','.join )
        }
    ]        

    for row in diselect(records, query):
        print(row)
