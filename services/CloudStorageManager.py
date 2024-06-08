from google.cloud import storage
import base64
import os
from io import BytesIO
from PIL import Image

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

    def download_file(self, bucket_name, source_blob_name, destination_file_name):
        """
        Downloads a blob from the bucket.

        :param source_blob_name: The name of the blob to download.
        :param destination_file_name: The name of the file to save the blob as.
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)

        try:
            blob.download_to_filename(destination_file_name)
            print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")
        except Exception as e:
            print(f"Failed to download {source_blob_name}: {e}")

    def delete_file(self, bucket_name, blob_name):
        """
        Deletes a blob from the bucket.

        :param blob_name: The name of the blob to delete.
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        try:
            blob.delete()
            print(f"Blob {blob_name} deleted.")
        except Exception as e:
            print(f"Failed to delete {blob_name}: {e}")


cloud_storage_manager = CloudStorageManager("drip-382808", "drip-bucket-1")
