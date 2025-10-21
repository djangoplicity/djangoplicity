from typing import Dict, List, Any

GEMINI_SLUG = 'gemini' # The slug used for the Gemini program and category
GEMINI_DOMAIN = 'media.gemini.edu'
DEFAULT_STORAGE_DOMAIN = 'storage.noirlab.edu'
TEST_DOMAIN = 'localhost:8000/public'


def replace_storage_domain(url: str, program: str):
    """
        Reeplace the domain 'storage.noirlab.edu' to 'media.gemini.edu'
        when the program is gemini. Used for img and video.
    """
    if not url:
        return url 

    if program == GEMINI_SLUG:
        url = url.replace(DEFAULT_STORAGE_DOMAIN, GEMINI_DOMAIN)
        return url
    
    return url


def has_gemini_category_request(request) -> bool:
    """
    Return True if the request query parameter `category` equals 'gemini'.
    """

    if not request:
        return False

    category_param = request.query_params.get('category')
    return isinstance(category_param, str) and category_param.lower() == GEMINI_SLUG


def has_gemini_program_request(request) -> bool:
    """
    Return True if the request query parameter `program` equals 'gemini'.
    Handles missing request or missing query_params gracefully.
    """
    if not request:
        return False

    program_param = request.query_params.get('program')
    return isinstance(program_param, str) and program_param.lower() == GEMINI_SLUG


def replace_gemini_domains(data: Dict[str, Any], key: str = GEMINI_SLUG) -> Dict[str, Any]:
    """
    Replace domains inside `formats` and `resources` fields if present.
    This is used by Image and Video serializers.
    """
    # Replace in formats
    if isinstance(data.get("formats"), dict):
        data["formats"] = {
            fmt: replace_storage_domain(url, key)
            for fmt, url in data["formats"].items()
        }

    # Replace in resources (for ImageSerializer)
    if isinstance(data.get("resources"), list):
        for res in data["resources"]:
            if "URL" in res:
                res["URL"] = replace_storage_domain(res["URL"], key)

    return data