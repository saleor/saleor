import re
from text_unidecode import unidecode


def to_const(string):
    return re.sub(r"[\W|^]+", "_", unidecode(string)).upper()
