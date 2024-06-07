from bson import ObjectId
from bson import datetime as bson_datetime
import json

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, bson_datetime.datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return obj
