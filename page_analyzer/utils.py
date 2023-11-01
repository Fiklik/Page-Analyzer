import validators
from urllib.parse import urlparse


def validate_url(url):
    return validators.url(url) and len(url) <= 255


def normalize_url(url):
    url = urlparse(url)
    return f'{url.scheme}://{url.netloc}'


def is_valid_status_code(code):
    return code < 400
