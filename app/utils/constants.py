# Google cloud storage base url
CLOUD_STORAGE_BASE_URL = "https://storage.googleapis.com"

# Profile picture bucket
DEFAULT_PROFILE_PICTURE = "https://storage.googleapis.com/drip-bucket-1/default_profile_pic.jpeg"
DEFAULT_BRAND_LOGO = "https://storage.googleapis.com/drip-bucket-1/default_brand_profile_pic.jpg"

# Brand search API base URL
BRAND_FETCH_BASE_URL = "https://api.brandfetch.io/v2/search/"

# Prompt for evaluating chat for misuse
ASSISTANT_MISUSE_PROMPT = (
    """
    You are an assistant evaluating whether the topic of a provided message is related to fashion. 
    is the following message related to fashion? answer yes or no.
    """
)

ASSISTANT_MISUSE_RESPONSE = "As a fashion assistant, I cannot answer this question."

# Prompt for Dalle image generation
ASSISTANT_IMAGE_GENERATION_PROMPT = (
    """
    You will be given a description of an outfit. Please create a picture that consists of a 
    single mannequin wearing all items in the described outfit. The background should be a chic 
    hardwood floored fitting room. The whole body of the mannequin should be shown. If multiple 
    colours are proposed for a particular clothing item, use the first colour in your depiction.

    Outfit description: \n\n
    """
)

# Prompt for extracting items from an outfit description
ASSISTANT_OUTFIT_ITEM_EXTRACTION_PROMPT = (
    """
    You are an LLM that analyzes an outfit description and identifies fashion items along with their 
    corresponding colors. Your task is to extract all individual items in the described outfit below
    and organize them by tops, bottoms, shoes, and accessories. If an item is described with multiple
    possible colors, produce separate entries in the output. Disregard any descriptive words that aren't 
    related to the name of the fashion item or its color. Here is an example of an input and output for 
    this task. Only produce the JSON in the output.

    Input:
    - Top: Light blue dress shirt with a slim collar and comfortable fit.
    - Bottoms: Dark gray or black slim-fit trousers or chinos for a sharp, yet relaxed look.
    - Shoes: Black or brown leather dress shoes, polished to perfection.
    - Accessories: Simple leather belt, slim watch, and a simple silver or leather cufflink.

    Output:
    {
        "tops": ["white sweater", "light blue sweater", "blush-colored dress shirt"],
        "bottoms": ["dark-washed jeans", "dark gray jeans", "dark gray chinos"],
        "shoes": ["black leather shoes", "loafers"]
        "accessories": ["leather belt", "slim watch", "silver cufflink", "leather cufflink"]
    }
    """
)

# Image Vision Prompt
ITEM_IMAGE_VISION_PROMPT = (
    """
    Describe the provided fashion item in detail focusing on the aspects outlined below. The description
    must be constrained to a 50-word limit:

    Color: Provide a vivid and descriptive explanation of the color, including any notable patterns or variations.

    Fabric: Describe the fabric in detail, including its texture, quality, and any unique characteristics.

    Occasions: Provide insights into suitable occasions for wearing this item. This may include events or seasons.
    """
)

OUTFIT_IMAGE_VISION_PROMPT = (
    """
    Describe the provided fashion outfit in detail focusing on the aspects outlined below. The description
    must be constrained to a 50-word limit:

    Items: Provide a vivid and descriptive explanation of the items in this outfit. Please focus on the colours
    and fabrics of all visible items and how they complement each other. Identify all visible tops, bottom, 
    shoes, and accessories.

    Occasions: Provide insights into suitable occasions for wearing this outfit.
    """
)