from google.cloud import secretmanager

class SecretManager:
    def __init__(self):
        self.project_number = "11431521918"
        self.client = secretmanager.SecretManagerServiceClient()

    def get_secret(self, secret_id, version_id="latest"):
        name = f"projects/{self.project_number}/secrets/{secret_id}/versions/{version_id}"
        response = self.client.access_secret_version(name=name)
        secret_value = response.payload.data.decode("UTF-8")
        return secret_value
