import os.path
import base64
from datetime import date, timedelta
from apiclient import errors
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
import re
from pprint import pprint

text_plain = "text/plain"
text_html = "text/html"

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


"""

Todo: if mimetype = multipart then we may have to go deeper into part nesting to get body and data
"""

def get_message(service, msg_id):

    try:
        message = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

        decoded_message = {}

        if len(message["payload"]["parts"]) > 0:
            for part in message["payload"]["parts"]:
                mime_type = part["mimeType"]
                if "data" in part["body"]:
                    data = part["body"]["data"]
                    decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
                    if mime_type == text_plain and text_plain not in decoded_message:
                        decoded_message[text_plain] = decoded_data
                    elif mime_type == text_html and text_html not in decoded_message:
                        decoded_message[text_html] = decoded_data
        else:
            mime_type = message["mimeType"]
            data = message["body"]["data"]
            if mime_type == text_plain and text_plain not in decoded_message:
                decoded_message[text_plain] = decoded_data
            elif mime_type == text_html and text_html not in decoded_message:
                decoded_message[text_html] = decoded_data

        return decoded_message
    except Exception as error:
        print("An error occurred in get_message: %s" % error)


def search_messages(service, search_string):

    try:
        search_ids = (
            service.users()
            .messages()
            .list(userId="me", q=search_string)
            .execute()
        )

        list_ids = []
        for msg_id in search_ids["messages"]:
            list_ids.append(msg_id["id"])
        return list_ids

    except errors.HttpError as error:
        print("An error occured in search_messages: %s" % error)


def authenticate():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def parse_html(email_html):
    soup = BeautifulSoup(email_html, 'html.parser')
    text = soup.prettify()
    with open('receipt.html', 'w') as f:
        f.write(text)

    item_map = {}
    categories = ["t-shirt", "shirt", "short", "pant", "shoes", "hoodie", "jacket", "coat", "jersey", "towel", "face covering"]

    # get item names from order
    item_names = []
    for category in categories:
        pattern = re.compile(r'\b' + re.escape(category) + r'\b', re.IGNORECASE)
        item_names.extend(soup.find_all(string=pattern))
    item_names = list(set(item_names))

    temp_names = []
    for element in item_names:
        cleaned_element = re.sub(r'^\s+|\s+$', '', element)
        temp_names.append(cleaned_element)
    item_names = temp_names

    # get item images
    for image in soup.find_all('img'):
        alt_text = image.get('alt', '').lower()
        for item_name in item_names:
            item_words = re.findall(r'\b\w+\b', item_name.lower())  # Extract individual words from item name
            matching_words = [word for word in item_words if word in alt_text]
            matching_percentage = len(matching_words) / len(item_words)
            if matching_percentage > 0.65:
                if item_name in item_map:
                    item_map[item_name].append(image['src'])
                else:
                    item_map[item_name] = [image['src']]

    # add items with no images to dictionary
    for item_name in item_names:
        if item_name not in item_map:
            item_map[item_name] = ["no image available"]

    # print results
    for item_name, item_images in item_map.items():
        print(f"Item: {item_name}")
        print(f"Images: {item_images}")
        print()

def main():
    receipt_key_words = '("(order OR purchase OR transaction) date" OR "date (ordered OR purchased)" "total" '
    item_key_words = '("shirt" OR "short" OR "pant" OR "shoes" OR "hoodie" OR "jacket" OR "coat") '
    #date_range = 'after:' + str(date.today() - timedelta(weeks=52))
    #search_string = receipt_key_words + item_key_words + date_range
    search_string = receipt_key_words + item_key_words
    creds = authenticate()
    service = build("gmail", "v1", credentials=creds)
    message_ids = search_messages(service, search_string)

    emails = []
    for message_id in message_ids:
        message = get_message(service, message_id)
        if message != {}:
            emails.append(message)

    parse_html(emails[2][text_html])

"""
    for email in emails:
        if text_html in email:
            parse_html(email[text_html])
            break
"""

if __name__ == "__main__":
    main()
