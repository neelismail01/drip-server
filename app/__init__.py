from flask import Flask
from pymongo import MongoClient
import certifi

from app.services.AssistantChatManager import AssistantChatManager
from app.services.ItemsManager import ItemsManager
from app.services.OutfitsManager import OutfitsManager
from app.services.SocialNetworkManager import SocialNetworkManager
from app.services.UserManager import UserManager

from app.services.CloudStorageManager import CloudStorageManager
from app.services.DalleManager import DalleManager
from app.services.GroqManager import GroqManager
from app.services.SecretManager import SecretManager
from app.services.TextEmbeddingManager import TextEmbeddingManager

from app.routes.brands import brands_blueprint
from app.routes.items import items_blueprint
from app.routes.outfits import outfits_blueprint
from app.routes.search import search_blueprint
from app.routes.user import user_blueprint
from app.routes.social import social_blueprint
from app.routes.assistant import assistant_blueprint

def create_app():
    # Initialize app
    app = Flask(__name__)

    # Get secrets
    secret_manager = SecretManager()
    MONGO_DB_URI = secret_manager.get_secret("MONGO_DB_URI")
    GROQ_API_KEY = secret_manager.get_secret("GROQ_API_KEY")
    OPENAI_API_KEY = secret_manager.get_secret("OPENAI_API_KEY")

    # Initialize the MongoDB client
    app.config['MONGODB_URI'] = MONGO_DB_URI
    mongo_client = MongoClient(app.config['MONGODB_URI'], tlsCAFile=certifi.where())
    app.mongo = mongo_client

    # Initialize DB service managers
    app.assistant_chat_manager = AssistantChatManager(app.mongo)
    app.items_manager = ItemsManager(app.mongo)
    app.outfits_manager = OutfitsManager(app.mongo)
    app.social_network_manager = SocialNetworkManager(app.mongo)
    app.user_manager = UserManager(app.mongo)

    # Initialize 3rd party service managers
    app.cloud_storage_manager = CloudStorageManager()
    app.dalle_manager = DalleManager(OPENAI_API_KEY)
    app.groq_manager = GroqManager(GROQ_API_KEY)
    app.text_embeddings_manager = TextEmbeddingManager(OPENAI_API_KEY)

    # Register blueprints with app
    app.register_blueprint(brands_blueprint, url_prefix="/brands")
    app.register_blueprint(items_blueprint, url_prefix="/items")
    app.register_blueprint(outfits_blueprint, url_prefix="/outfits")
    app.register_blueprint(search_blueprint, url_prefix="/search")
    app.register_blueprint(social_blueprint, url_prefix='/social')
    app.register_blueprint(user_blueprint, url_prefix='/user')
    app.register_blueprint(assistant_blueprint, url_prefix="/assistant")

    return app
