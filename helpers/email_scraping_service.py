import os.path
import base64
from datetime import date, timedelta
from apiclient import errors
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup, SoupStrainer, Comment
import re
from pprint import pprint

text_plain = "text/plain"
text_html = "text/html"

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


"""
Todo:
- if mimetype = multipart then we may have to go deeper into part nesting to get body and data
- get brand name from sender email (string before .com or .ca)
"""

def get_message(service, msg_id, user_email_address):

    try:
        message = (
            service.users()
            .messages()
            .get(userId=user_email_address, id=msg_id, format="full")
            .execute()
        )

        email = {}
        decoded_message = {}
        brand = ""

        for header in message["payload"]["headers"]:
            if header["name"] == "From":
                sender = header["value"].split('<', 1)[0].strip()
                sender = sender.replace("\\", "")
                sender = re.sub(r'"', '', sender)
                if "@" in sender:
                    if ".com" in sender:
                        at_index = sender.find("@")
                        com_index = sender.find(".com")
                        brand = sender[at_index + 1:com_index]
                    else:
                        at_index = sender.find("@")
                        com_index = sender.find(".ca")
                        brand = sender[at_index + 1:com_index]
                else:
                    brand = sender

        if "parts" in message["payload"]:
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


        email["decoded_message"] = decoded_message
        email["brand"] = ' '.join(word.capitalize() for word in brand.split())

        return email
    except Exception as error:
        print("An error occurred in get_message: %s" % error)


def search_messages(service, search_string, user_email_address):

    try:
        search_ids = (
            service.users()
            .messages()
            .list(userId=user_email_address, q=search_string)
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

def parse_html(email):

    email_html = email["decoded_message"][text_html]
    brand = email["brand"]

    # function that will disregard any item matches in html code that has been commented out
    def is_visible(element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    soup = BeautifulSoup(email_html, 'html.parser')
    text = soup.prettify()

    # create html file for email
    with open('receipt.html', 'w') as f:
        f.write(text)

    categories = ["t-shirt", "tee", "shirt", "short", "shorts", "pant", "pants", "shoes", "shoe", "hoodie", 
                "sweater", "sweatshirt", "crewneck", "jacket", "coat", "jersey", "towel", "face covering", "linen",
                "jean", "jeans", "khaki", "khakis", "chino", "chinos", "pajamas", "dress shirt", "polo shirt", "robe", 
                "swim trunks", "swim shorts", "socks", "sneaker", "sneakers", "boots", "boot", "sandals", "sandal", "flip-flops", "loafers", 
                "slippers", "hat", "belt", "backpack", "scarf", "sunglasses", "tie", "necklace", "chain", "cap", "boxer", "boxers",
                "bracelet", "bracelets", "cardigan", "denim", "earring", "earrings", "glove", "gloves", "handbag", "handbags", "legging",
                "leggings", "leotard", "leotards", "tights", "lingerie", "dress", "dresses", "blouse", "skirt", "skirts", "raincoat", "raincoats",
                "parka", "parkas", "sleepwear", "sportswear", "stilletos", "stiletto", "bodysuit", "suit", "swimwear", "tuxedo", 
                "tracksuit", "cufflinks", "cufflink", "purse", "tuque", "flannel"]
    
    item_types = ["accessories", "watches", "jewelry", "cosmetics", "formal wear", "footwear", "outerwear", "tops", "bottoms"]
    
    accessories = ["tie", "cufflink", "cufflinks", "handbag", "purse", "hat", "cap", "tuque", "glove", "gloves", "belt", 
                   "suspender", "suspenders", "eyewear", "glasses", "sunglasses", "wallet", "socks", "stockings"]
    watches = ["watch"]
    jewelry = ["earring", "earrings", "necklace", "bracelet", "ring", "chain"]
    cosmetics = ["makeup", "beauty products", "hair products", "skin cleansers", "lotion", "perfume", "cologne"]
    formal_wear = ["suit", "tuxedo"]
    footwear = ["boot", "boots", "shoe", "shoes", "sandal", "sandals", "loafer", "loafers", "flip-flops", 
                "slipper", "slippers", "sneaker", "sneakers", "stilettos"]
    outerwear = ["parka", "raincoat", "cardigan", "coat", "jacket"]
    tops = ["blouse", "polo", "shirt", "t-shirt", "tee", "dress shirt", "hoodie", "jersey", "crewneck", "sweater", 
            "sweatshirt", "flannel", "linen"]
    bottoms = ["skirt", "khaki", "khakis", "pant", "pants", "sweatpant", "sweatpants", "chino", "chinos", "jeans", 
               "jean", "tights", "leggings", "swim shorts", "swim trunks", "short", "shorts"]
    
    item_map = {}

    # get item names from order and remove duplicates
    item_names = []
    for category in categories:
        pattern = re.compile(r'\b' + re.escape(category) + r'\b', re.IGNORECASE)
        matches = soup.find_all(string=pattern)
        visible_matches = [match for match in matches if is_visible(match)]
        item_names.extend(visible_matches)
    
    # get rid of any extra items found that are just a category (i.e. standalone string "pants" exists somewhere in email)
    filtered_item_names = [item_name for item_name in item_names if item_name.lower() not in categories]
    
    # remove duplicates
    item_names = list(set(filtered_item_names))

    # remove any white space before or after the item names
    temp_names = []
    for element in item_names:
        cleaned_element = re.sub(r'^\s+|\s+$', '', element)
        temp_names.append(cleaned_element)
    item_names = temp_names

    # get item images => map item names to item images
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

    # Convert the item map to an array of item dictionaries
    order_items = [{'item_name': key, 'images': value} for key, value in item_map.items()]
    raw_order = {}
    raw_order[brand] = order_items

    # final output cleaned up
    order = {}
    for brand, items in raw_order.items():
        order["brand"] = brand
        order["items"] = items

    items = []

    for item in order["items"]:
        to_add = {}
        to_add["brand"] = brand
        to_add["item_name"] = item["item_name"]
        to_add["images"] = item["images"]
        items.append(to_add)

    # add inital tag
    for item in items:
        item_name = item['item_name'].lower()
        for category in categories:
            if category in item_name:
                item['tags'] = [category]
                break

    
    def determine_item_type(tag):
        for item_type, item_type_list in zip(item_types, [accessories, watches, jewelry, cosmetics, formal_wear, footwear, outerwear, tops, bottoms]):
            if tag in item_type_list:
                return item_type
        return None  # If no item type is found

    # add broader category to list of tags
    for item in items:
        item_tag = item["tags"][0]
        item_type = determine_item_type(item_tag)
        if item_type:
            item["tags"] = [item_type, item_tag]

    # get the html tags of all the items
    item_tags = []
    for category in categories:
        pattern = re.compile(r'\b' + re.escape(category) + r'\b', re.IGNORECASE)
        matches = soup.find_all(string=pattern)
        visible_matches = [match for match in matches if is_visible(match)]
        item_tags.extend(visible_matches)

    filtered_item_tags = [item_tag for item_tag in item_tags if item_tag.lower() not in categories]

    # check if item is an <a> tag, if so then we can extract the product page link
    for item_tag in filtered_item_tags:
        for item in items:
            if item_tag.get_text().strip() == item["item_name"] and item_tag.find_parent().name == 'a':
                href_value = item_tag.find_parent().get('href')
                item["product_page_link"] = href_value
                break

    return items

    """
    This is what each order looks like as returned by the function

    {
        brand: "Lululemon",
        item_name: "Commission Slim-Fit Pant 32" *Warpstreme",
        images: ['https://images.lululemon.com/is/image/lululemon/LM5AF2S_032476_1']
        tag = ["pant"]
    }
    """

def get_product_page_link(brand, product_name):
    API_KEY = "AIzaSyDLvRwgY8OXyNb4a7bas4aT-gXQvHkRwTE"
    SEARCH_ENGINE_ID = "d1062150d54a04ec6"

    brand = "".join(brand.split()).lower()
    product_name = product_name.lower()

    query = brand + " " + product_name

    service = build(
        "customsearch", "v1", developerKey=API_KEY
    )

    result = service.cse().list(
        q=query,
        cx=SEARCH_ENGINE_ID
    ).execute()

    brand_website_base_link = None
    if "items" in result:
        for item in result['items']:
            link = item['link']
            link_match = re.match("(.*)(\.com|\.ca)(.*)", link)
            if link_match:
                brand_in_link = brand in link_match.group(1)

                product_name_in_link = False
                product_name_words_in_link = 0
                for word in product_name:
                    if word in link_match.group(3):
                        product_name_words_in_link += 1
                if product_name_words_in_link / len(product_name) > 0.5:
                    product_name_in_link = True
                
                if brand_in_link and product_name_in_link:
                    return link
                if not brand_website_base_link and brand_in_link:
                    brand_website_base_link = link_match.group(1) + link_match.group(2)

    return brand_website_base_link

def get_items(user_email_address):
    query = '("order" OR "purchase" OR "transaction") subject:(receipt OR invoice OR confirmation OR order OR confirmed OR processed OR shipped OR delivery) (tuxedos OR tracksuits OR swimwear OR suits OR stilettos OR sportswear OR skirts OR sleepwear OR parkas OR panties OR raincoats OR lingerie OR tights OR leotards OR leggings OR handbags OR gloves OR earrings OR denim OR cardigan OR bracelets OR boxers OR cap OR khakis OR chinos OR pyjamas OR robe OR polo OR swim OR socks OR boots OR sneakers OR sandals OR flip-flops OR loafers OR slippers OR hat OR belt OR backpack OR scarf OR sunglasses OR tie OR necklace OR chain OR shirt OR tee OR shorts OR short OR pants OR pant OR shoes OR hoodie OR sweater OR sweatshirt OR jacket OR coat OR jean) -has:attachment -(unsubscribe) -(“manage preferences”) -(“email preferences”) -("manage emails")'
    #query = '("order" OR "purchase" OR "transaction") subject:(receipt OR invoice OR confirmation OR order OR confirmed OR processed OR shipped OR delivery) (craftd) -has:attachment -(unsubscribe) -(“manage preferences”) -(“email preferences”) -("manage emails")'
    """body_key_words = '("order" OR "purchase" OR "transaction")'
    date_key_words = '("(order OR purchase OR transaction) date" OR "date (ordered OR purchased)" "total"'
    subject_key_words = 'subject:(receipt OR invoice OR confirmation OR order OR confirmed OR processed OR shipped OR delivery)'
    item_key_words = '(tuxedos OR tracksuits OR swimwear OR suits OR stilettos OR sportswear OR skirts OR sleepwear OR parkas OR panties OR raincoats OR lingerie OR tights OR leotards OR leggings OR handbags OR gloves OR earrings OR denim OR cardigan OR bracelets OR boxers OR cap OR khakis OR chinos OR pyjamas OR robe OR polo OR swim OR socks OR boots OR sneakers OR sandals OR flip-flops OR loafers OR slippers OR hat OR belt OR backpack OR scarf OR sunglasses OR tie OR necklace OR chain OR shirt OR tee OR shorts OR short OR pants OR pant OR shoes OR hoodie OR sweater OR sweatshirt OR jacket OR coat OR jean)'
    exclude = '-subject:(Fwd: OR Forwarded) -cc:youremail@gmail.com -bcc:youremail@gmail.com -has:attachment -(unsubscribe) -(“manage preferences”) -(“email preferences”) -("manage emails")'
    date_range = 'after:' + str(date.today() - timedelta(weeks=52))
    search_string = body_key_words + subject_key_words + item_key_words + exclude"""
    search_string = query
    creds = authenticate()
    service = build("gmail", "v1", credentials=creds)
    message_ids = search_messages(service, search_string, user_email_address)

    emails = []
    for message_id in message_ids:
        email = get_message(service, message_id, user_email_address)
        if email["decoded_message"] != {}:
            emails.append(email)

    total_items = []
    for email in emails:
        if text_html in email["decoded_message"]:
            items = parse_html(email)
            for item in items:
                total_items.append(item)

    for item in total_items:
        if "product_page_link" not in item or not item["product_page_link"]:
            item["product_page_link"] = get_product_page_link(item["brand"], item["item_name"])

    # remove duplicate items
    unique_item_names = set()
    unique_items = []
    for item in total_items:
        if item['item_name'] not in unique_item_names:
            unique_item_names.add(item['item_name'])
            unique_items.append(item)

    return unique_items
