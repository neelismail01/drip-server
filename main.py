from flask import (
    Flask
)
from flask_session import Session
from flask_cors import CORS
from pymongo import MongoClient
import os
import certifi

from services.GroqManager import GroqManager
from services.DalleManager import DalleManager

from routes.brands import brands_blueprint
from routes.items import items_blueprint
from routes.outfits import outfits_blueprint
from routes.search import search_blueprint
from routes.user import user_blueprint
from routes.social import social_blueprint
from routes.assistant import assistant_blueprint

from constants import MONGO_URI

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['MONGO_URI'] = MONGO_URI

# Initialize the MongoDB client
mongo_client = MongoClient(app.config['MONGO_URI'], tlsCAFile=certifi.where())
app.mongo = mongo_client

# Initialize the GroqManager
app.groq_manager = GroqManager(os.environ.get("GROQ_API_KEY"))

# Initialize the DalleManager
app.dalle_manager = DalleManager()

Session(app)
cors = CORS(app)

# Register the blueprint with the app
app.register_blueprint(brands_blueprint, url_prefix="/brands")
app.register_blueprint(items_blueprint, url_prefix="/items")
app.register_blueprint(outfits_blueprint, url_prefix="/outfits")
app.register_blueprint(search_blueprint, url_prefix="/search")
app.register_blueprint(social_blueprint, url_prefix='/social')
app.register_blueprint(user_blueprint, url_prefix='/user')
app.register_blueprint(assistant_blueprint, url_prefix="/assistant")

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, port=8080)
