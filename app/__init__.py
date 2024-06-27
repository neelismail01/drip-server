from flask import Flask
from pymongo import MongoClient
import certifi

from app.services.internal.AssistantChatManager import AssistantChatManager
from app.services.internal.ItemsManager import ItemsManager
from app.services.internal.OutfitsManager import OutfitsManager
from app.services.internal.SearchManager import SearchManager
from app.services.internal.SocialNetworkManager import SocialNetworkManager
from app.services.internal.UserManager import UserManager

from app.services.external.BrandSearchManager import BrandSearchManager
from app.services.external.CloudStorageManager import CloudStorageManager
from app.services.external.CustomSearchManager import CustomSearchManager
from app.services.external.DalleManager import DalleManager
from app.services.external.GroqManager import GroqManager
from app.services.external.ImageVisionManager import ImageVisionManager
from app.services.external.SecretManager import SecretManager
from app.services.external.TextEmbeddingManager import TextEmbeddingManager

from app.routes.assistant import assistant_blueprint
from app.routes.brands import brands_blueprint
from app.routes.file_upload import file_upload_blueprint
from app.routes.items import items_blueprint
from app.routes.outfits import outfits_blueprint
from app.routes.search import search_blueprint
from app.routes.social import social_blueprint
from app.routes.user import user_blueprint

def create_app():
    # Initialize app
    app = Flask(__name__)

    # Get secrets
    secret_manager = SecretManager()
    BRAND_SEARCH_API_KEY = secret_manager.get_secret("BRAND_SEARCH_API_KEY")
    GOOGLE_CUSTOM_SEARCH_API_KEY = secret_manager.get_secret("GOOGLE_CUSTOM_SEARCH_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID = secret_manager.get_secret("GOOGLE_SEARCH_ENGINE_ID")
    GROQ_API_KEY = secret_manager.get_secret("GROQ_API_KEY")
    MONGO_DB_URI = secret_manager.get_secret("MONGO_DB_URI")
    OPENAI_API_KEY = secret_manager.get_secret("OPENAI_API_KEY")
    PRESIGNED_URL_SERVICE_ACCOUNT_JSON = secret_manager.get_secret("PRESIGNED_URL_SERVICE_ACCOUNT_JSON")

    # Initialize the MongoDB client
    app.config['MONGODB_URI'] = MONGO_DB_URI
    mongo_client = MongoClient(app.config['MONGODB_URI'], tlsCAFile=certifi.where())
    app.mongo = mongo_client

    # Initialize DB service managers
    app.assistant_chat_manager = AssistantChatManager(app.mongo)
    app.items_manager = ItemsManager(app.mongo)
    app.outfits_manager = OutfitsManager(app.mongo)
    app.search_manager = SearchManager(app.mongo)
    app.social_network_manager = SocialNetworkManager(app.mongo)
    app.user_manager = UserManager(app.mongo)

    # Initialize 3rd party service managers
    app.brand_search_manager = BrandSearchManager(BRAND_SEARCH_API_KEY)
    app.cloud_storage_manager = CloudStorageManager(PRESIGNED_URL_SERVICE_ACCOUNT_JSON)
    app.custom_search_manager = CustomSearchManager(GOOGLE_CUSTOM_SEARCH_API_KEY, GOOGLE_SEARCH_ENGINE_ID)
    app.dalle_manager = DalleManager(OPENAI_API_KEY)
    app.groq_manager = GroqManager(GROQ_API_KEY)
    app.image_vision_manager = ImageVisionManager(OPENAI_API_KEY)
    app.text_embeddings_manager = TextEmbeddingManager(OPENAI_API_KEY, OPENAI_API_KEY)

    # Register blueprints with app
    app.register_blueprint(assistant_blueprint, url_prefix="/assistant")
    app.register_blueprint(brands_blueprint, url_prefix="/brands")
    app.register_blueprint(file_upload_blueprint, url_prefix="/file_upload")
    app.register_blueprint(items_blueprint, url_prefix="/items")
    app.register_blueprint(outfits_blueprint, url_prefix="/outfits")
    app.register_blueprint(search_blueprint, url_prefix="/search")
    app.register_blueprint(social_blueprint, url_prefix="/social")
    app.register_blueprint(user_blueprint, url_prefix="/user")

    return app
