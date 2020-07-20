from .transliteration import transliterate
from .slugify import slugify


def transliterate_name(_data):
    return transliterate(_data.replace('.', ""))


def slugify_name(_data):
    return slugify(_data.replace('/', "-"))
