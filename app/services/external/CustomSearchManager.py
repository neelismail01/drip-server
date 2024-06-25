
from googleapiclient.discovery import build
import re
import tldextract

class CustomSearchManager:
    def __init__(self, api_key, search_engine_id):
        self.api_key = api_key
        self.search_engine_id = search_engine_id

    def get_brand_website_domain(self, brand):
        query = "{} official website".format(brand.lower())
        service = build("customsearch", "v1", developerKey=self.api_key)
        result = service.cse().list(q=query, cx=self.search_engine_id).execute()
        if "items" in result:
            for item in result['items']:
                if re.search("(^https?://(?:www\.)?{}[^/]*\.[a-z]+)".format(re.escape(brand)), item['link']):
                    extracted = tldextract.extract(item['link'])
                    domain = f"{extracted.domain}.{extracted.suffix}"
                    return domain
        return None