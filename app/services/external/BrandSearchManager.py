import requests
from app.utils.constants import BRAND_FETCH_BASE_URL

class BrandSearchManager():
    def __init__(self, api_key):
        self.api_key = api_key

    def search_brands(self, query):
        url = "{}{}".format(BRAND_FETCH_BASE_URL, query)
        authorization = "Bearer {}".format(self.api_key)
        response = requests.get(url, headers={
            "accept": "application/json",
            "Authorization": authorization
        })
        if response.status_code == 200:
            return response.json(), 200
        return { "error": "Failed to fetch brand data" }, response.status_code
