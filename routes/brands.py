from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)

from bson.json_util import dumps

brands_blueprint = Blueprint('brands', __name__)

@brands_blueprint.route('/', methods=["GET"])
def all_brands():
    db = current_app.mongo.drip
    collection = db['brands']
    if request.method == "GET":
        brands = list(collection.find().sort('purchaseCount', -1))
        json_brands = dumps(brands)
        return json_brands, 201
    
@brands_blueprint.route('/<brand_name>', methods=["GET"])
def brand(brand_name):
    db = current_app.mongo.drip
    collection = db['brands']
    if request.method == "GET":
        brand = collection.find_one({'brand_name': brand_name})
        if not brand:
            return {}, 200
        brand['_id'] = str(brand['_id'])
        return jsonify(brand), 200
    
@brands_blueprint.route('/outfit_brands', methods=["GET"])
def outfit_brands():
    db = current_app.mongo.drip
    collection = db['brands']
    if request.method == "GET":
        brand_names = request.args.getlist("brand_names[]")
        query = {"brand_name": {"$in": brand_names}}
        brands = list(collection.find(query))
        for brand in brands:
            brand['_id'] = str(brand['_id'])
        return jsonify(brands), 200

