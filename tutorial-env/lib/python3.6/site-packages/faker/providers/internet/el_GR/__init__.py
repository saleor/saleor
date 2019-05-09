# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as InternetProvider

import re
from faker.utils.decorators import slugify_domain


class Provider(InternetProvider):

    free_email_domains = (
        'hol.gr', 'gmail.com', 'hotmail.gr', 'yahoo.gr', 'googlemail.gr',
        'otenet.gr', 'forthnet.gr',
    )
    tlds = ('com', 'com', 'com', 'net', 'org', 'gr', 'gr', 'gr')

    @slugify_domain
    def user_name(self):
        pattern = self.random_element(self.user_name_formats)
        return latinize(self.bothify(self.generator.parse(pattern)))

    @slugify_domain
    def domain_word(self):
        company = self.generator.format('company')
        company_elements = company.split(' ')
        company = latinize(company_elements.pop(0))
        return company


# ``slugify`` doesn't replace greek glyphs.

def remove_accents(value):
    """
    Remove accents from characters in the given string.
    """
    search = 'ΆΈΉΊΌΎΏάέήίόύώΪϊΐϋΰ'
    replace = 'ΑΕΗΙΟΥΩαεηιουωΙιιυυ'

    def replace_accented_character(match):
        matched = match.group(0)
        if matched in search:
            return replace[search.find(matched)]
        return matched

    return re.sub(r'[{0}]+'.format(search), replace_accented_character, value)


def latinize(value):
    """
    Converts (transliterates) greek letters to latin equivalents.
    """
    def replace_double_character(match):
        search = ('Θ Χ Ψ '
                  'θ χ ψ '
                  'ΟΥ ΑΥ ΕΥ '
                  'Ου Αυ Ευ '
                  'ου αυ ευ').split()
        replace = ('TH CH PS '
                   'th ch ps '
                   'OU AU EU '
                   'Ou Au Eu '
                   'ou au eu').split()
        matched = match.group(0)
        if matched in search:
            return replace[search.index(matched)]
        return matched

    search = 'ΑΒΓΔΕΖΗΙΚΛΜΝΞΟΠΡΣΣΤΥΦΩαβγδεζηικλμνξοπρσςτυφω'
    replace = 'AVGDEZIIKLMNXOPRSSTUFOavgdeziiklmnxoprsstyfo'

    def replace_greek_character(match):
        matched = list(match.group(0))
        value = map(lambda l: replace[search.find(l)], matched)
        return ''.join(value)

    return re.sub(r'[{0}]+'.format(search),
                  replace_greek_character, re.sub(
        r'([ΘΧΨθχψ]+|ΟΥ|ΑΥ|ΕΥ|Ου|Αυ|Ευ|ου|αυ|ευ)',
        replace_double_character,
        remove_accents(value)))
