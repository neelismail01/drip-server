from google.cloud import storage
import base64
import os
from io import BytesIO
from PIL import Image

class CloudStorageManager:
    def __init__(self):
        self.client = storage.Client(project="drip-382808")

    def upload_file(self, bucket_name, file_path, destination_blob_name):
        """
        Uploads a file to the bucket.

        :param file_path: The path to the file to upload.
        :param destination_blob_name: The name of the blob to store the file in.
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        try:
            blob.upload_from_filename(file_path)
            blob.make_public()  # Make the file publicly accessible
            print(f"File {file_path} uploaded to {destination_blob_name}.")
            return blob.public_url
        except Exception as e:
            print(f"Failed to upload {file_path}: {e}")
            return None

    def upload_base64_file(self, bucket_name, base64_string, destination_blob_name):
        """
        Uploads a base64 encoded file to the bucket, converts it to PNG, and returns the public URL.

        :param base64_string: The base64 encoded string of the file.
        :param destination_blob_name: The name of the blob to store the file in.
        :return: The public URL of the uploaded file.
        """
        try:
            # Decode the base64 string and convert it to a PNG image
            image_data = base64.b64decode(base64_string)
            image = Image.open(BytesIO(image_data))
            temp_file_path = f"/tmp/{destination_blob_name}.png"
            image.save(temp_file_path, format="PNG")

            # Upload the PNG image
            public_url = self.upload_file(bucket_name, temp_file_path, f"{destination_blob_name}.png")

            # Remove the temporary file
            os.remove(temp_file_path)

            return public_url
        except Exception as e:
            print(f"Failed to upload base64 file: {e}")
            return None

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
