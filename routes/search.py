import requests

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)

search_blueprint = Blueprint('search', __name__)

index_fields = {
    'item_searchindex': ['item_name', 'brand', 'tag'],
    'user_searchindex': ['name', 'email'],
    'brand_searchindex': ['brand_name']
}

autocomplete_index_fields = {
    'item_autocomplete_searchindex': 'item_name',
    'user_autocomplete_searchindex': 'name',
    'brand_autocomplete_searchindex': 'brand_name'
}

def init_search(query, index_name, index_fields):
    path = index_fields.get(index_name)

    search_engine = [
        {
            '$search': {
                'index': index_name,
                'text': {
                    'query': query,
                    'path': path,
                }
            }
        }
    ]

    return search_engine

def init_search_autocomplete(query, index_name, autocomplete_index_fields):
    path = autocomplete_index_fields.get(index_name)

    search_engine = [
        {
            '$search': {
                "index": index_name,
                "autocomplete": {
                    "query": query,
                    "path": path,
                    "tokenOrder": "sequential",
                    "fuzzy": {}
                }
            }
        },
        {
            '$limit': 10
        }
    ]

    return search_engine

@search_blueprint.route('/search', methods=['GET'])
def search():
    db = current_app.mongo.drip

    index_collections = {
        'item_searchindex': db['items'],
        'brand_searchindex': db['brands'],
        'user_searchindex': db['users']
    }
    query = request.args.get('query')
    index_name = request.args.get('index')
    collection = index_collections.get(index_name)
    search_engine = init_search(query, index_name, index_fields)
    search_results = list(collection.aggregate(search_engine))
    for result in search_results:
        result['_id'] = str(result['_id'])
    return jsonify(search_results)

@search_blueprint.route('/autocomplete_search', methods=['GET'])
def autocomplete_search():
    db = current_app.mongo.drip

    index_collections = {
        'item_autocomplete_searchindex': db['items'],
        'brand_autocomplete_searchindex': db['brands'],
        'user_autocomplete_searchindex': db['users']
    }
    query = request.args.get('query')
    index_name = request.args.get('index')
    collection = index_collections.get(index_name)
    search_engine = init_search_autocomplete(query, index_name, autocomplete_index_fields)
    search_results = list(collection.aggregate(search_engine))
    for result in search_results:
        result['_id'] = str(result['_id'])
    return jsonify(search_results)
