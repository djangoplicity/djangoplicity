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


def has_gemini_category(categories: List[Dict[str, Any]]) -> bool:
    """Return True if any category dict has slug 'gemini'."""
    return any(
        cat.get("slug", "").lower() == GEMINI_SLUG 
        for cat in (categories or [])
    )


def has_gemini_program(programs) -> bool:
    """Return True if any related program has slug 'gemini'."""
    return any(
        getattr(p, "url", "").lower() == GEMINI_SLUG 
        for p in programs
    )

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