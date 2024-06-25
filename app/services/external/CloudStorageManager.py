from google.cloud import storage
import base64
from datetime import datetime

class CloudStorageManager:
    def __init__(self):
      self.client = storage.Client(project="drip-382808")
      self.bucket = self.client.bucket("drip-bucket-1")

    def upload_media_to_gcs(self, image_data, destination_blob_name, content_type):
      blob = self.bucket.blob(destination_blob_name)
      # Upload the image data to GCS
      blob.upload_from_string(image_data, content_type=content_type)
      # Get the URL of the uploaded image
      return blob.public_url

    def upload_multiple_media_to_gcs(self, pictures, user_id):
      media_urls = []
      for media in pictures:
        if media["type"] == "image":
          image_bytes = base64.b64decode(media["data"])
          destination = "item_{}_{}".format(user_id, str(datetime.now()))
          gcs_media_url = self.upload_media_to_gcs(image_bytes, destination, 'image/jpeg')
          media_urls.append(gcs_media_url)
        else:
          print("Unsupported media format")
      return media_urls

cloud_storage_manager = CloudStorageManager()
