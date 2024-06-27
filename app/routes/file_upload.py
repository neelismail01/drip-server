
import json
from flask import (
    current_app,
    Blueprint,
    request
)
from app.utils.MongoJsonEncoder import MongoJSONEncoder

file_upload_blueprint = Blueprint("file_upload", __name__)

@file_upload_blueprint.route("/get_signed_url", methods=["POST"])
def get_signed_url():
    data = request.json
    file_name, file_type = data.get("fileName"), data.get("fileType")
    signed_url = current_app.cloud_storage_manager.get_signed_url(file_name, file_type)
    return json.dumps(signed_url, cls=MongoJSONEncoder)
