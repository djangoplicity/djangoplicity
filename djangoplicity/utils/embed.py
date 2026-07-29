from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


def embed_url(url, is_embed):
    """
    Appends "?embed=true" (or "&embed=true") to url when is_embed is truthy.

    Handles edge cases:
    - Uses "&" if URL already has query params
    - Preserves fragment ("#section")
    - Avoids duplication if "embed=true" already present

    Usage:
        url = embed_url('/foo/', True)       # -> /foo/?embed=true
        url = embed_url('/foo?x=1', True)    # -> /foo?x=1&embed=true
        url = embed_url('/foo#sec', True)    # -> /foo/?embed=true#sec
        url = embed_url('/foo/', False)      # -> /foo/
    """
    if not is_embed:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if 'embed' in query:
        return url
    query['embed'] = ['true']
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))
