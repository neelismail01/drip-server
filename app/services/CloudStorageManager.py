from google.cloud import storage

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

cloud_storage_manager = CloudStorageManager()
