from google.cloud import storage

class CloudStorageManager:
    def __init__(self, project_name, bucket_name):
        self.client = storage.Client(project=project_name)
        self.bucket = self.client.bucket(bucket_name)

    def upload_media_to_gcs(self, image_data, destination_blob_name, content_type):
        blob = self.bucket.blob(destination_blob_name)
        # Upload the image data to GCS
        blob.upload_from_string(image_data, content_type=content_type)
        # Get the URL of the uploaded image
        return blob.public_url

cloud_storage_manager = CloudStorageManager("drip-382808", "drip-bucket-1")
