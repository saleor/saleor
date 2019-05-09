# coding=utf-8

from __future__ import unicode_literals
from .. import BaseProvider
from .isbn import ISBN, ISBN10, ISBN13
from .rules import RULES


class Provider(BaseProvider):
    """ Generates fake ISBNs. ISBN rules vary across languages/regions
    so this class makes no attempt at replicating all of the rules. It
    only replicates the 978 EAN prefix for the English registration
    groups, meaning the first 4 digits of the ISBN-13 will either be
    978-0 or 978-1. Since we are only replicating 978 prefixes, every
    ISBN-13 will have a direct mapping to an ISBN-10.

    See https://www.isbn-international.org/content/what-isbn for the
    format of ISBNs.
    See https://www.isbn-international.org/range_file_generation for the
    list of rules pertaining to each prefix/registration group.
    """

    def _body(self):
        """ Generate the information required to create an ISBN-10 or
        ISBN-13.
        """
        ean = self.random_element(RULES.keys())
        reg_group = self.random_element(RULES[ean].keys())

        # Given the chosen ean/group, decide how long the
        #   registrant/publication string may be.
        # We must allocate for the calculated check digit, so
        #   subtract 1
        reg_pub_len = ISBN.MAX_LENGTH - len(ean) - len(reg_group) - 1

        # Generate a registrant/publication combination
        reg_pub = self.numerify('#' * reg_pub_len)

        # Use rules to separate the registrant from the publication
        rules = RULES[ean][reg_group]
        registrant, publication = self._registrant_publication(reg_pub, rules)
        return [ean, reg_group, registrant, publication]

    @staticmethod
    def _registrant_publication(reg_pub, rules):
        """ Separate the registration from the publication in a given
        string.
        :param reg_pub: A string of digits representing a registration
            and publication.
        :param rules: A list of RegistrantRules which designate where
            to separate the values in the string.
        :returns: A (registrant, publication) tuple of strings.
        """
        for rule in rules:
            if rule.min <= reg_pub <= rule.max:
                reg_len = rule.registrant_length
                break
        else:
            raise Exception('Registrant/Publication not found in registrant '
                            'rule list.')
        registrant, publication = reg_pub[:reg_len], reg_pub[reg_len:]
        return registrant, publication

    def isbn13(self, separator='-'):
        ean, group, registrant, publication = self._body()
        isbn = ISBN13(ean, group, registrant, publication)
        return isbn.format(separator)

    def isbn10(self, separator='-'):
        ean, group, registrant, publication = self._body()
        isbn = ISBN10(ean, group, registrant, publication)
        return isbn.format(separator)
