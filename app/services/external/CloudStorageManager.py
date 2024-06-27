from google.cloud import storage
from google.oauth2 import service_account
from google import auth
import base64
import json
from datetime import datetime, timedelta

class CloudStorageManager:
    def __init__(self, presigned_url_json):
      _, project_id = auth.default()
      self.client = storage.Client(project=project_id)
      self.bucket = self.client.bucket("drip-bucket-1")
      self.presigned_url_service_account_creds = service_account.Credentials.from_service_account_info(
        json.loads(presigned_url_json)
      )

    def upload_media_to_gcs(self, image_data, destination_blob_name, content_type):
      blob = self.bucket.blob(destination_blob_name)
      blob.upload_from_string(image_data, content_type=content_type)
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

    def get_signed_url(self, file_name, file_type):
      try:
        blob = self.bucket.blob(file_name)
        signed_url = blob.generate_signed_url(
          version='v4',
          expiration=timedelta(hours=1),
          method="PUT",
          content_type=file_type,
          credentials=self.presigned_url_service_account_creds
        )
        return signed_url
      except Exception as e:
        return None
