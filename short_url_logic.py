import pyshorteners
from os import environ

TINY_URL_API_TOKEN = environ['TINY_URL_API_TOKEN']



def shorten_url(url) -> str:
    """
    Shorten a url using the pyshorteners library
    :param url: url to shorten
    :return: shortened url
    """
    s = pyshorteners.Shortener(api_key=TINY_URL_API_TOKEN)

    return s.tinyurl.short(url)


