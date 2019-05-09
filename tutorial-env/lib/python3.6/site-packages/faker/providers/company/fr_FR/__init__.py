# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{last_name}} {{last_name}} {{company_suffix}}',
        '{{last_name}}',
        '{{last_name}}',
    )

    catch_phrase_formats = (
        '{{catch_phrase_noun}} {{catch_phrase_verb}} {{catch_phrase_attribute}}', )

    nouns = (
        'la sécurité',
        'le plaisir',
        'le confort',
        'la simplicité',
        "l'assurance",
        "l'art",
        'le pouvoir',
        'le droit',
        'la possibilité',
        "l'avantage",
        'la liberté')

    verbs = (
        'de rouler',
        "d'avancer",
        "d'évoluer",
        'de changer',
        "d'innover",
        'de louer',
        "d'atteindre vos buts",
        'de concrétiser vos projets')

    attributes = (
        'de manière efficace',
        'plus rapidement',
        'plus facilement',
        'plus simplement',
        'en toute tranquilité',
        'avant-tout',
        'autrement',
        'naturellement',
        'à la pointe',
        'sans soucis',
        "à l'état pur",
        'à sa source',
        'de manière sûre',
        'en toute sécurité')

    company_suffixes = ('SA', 'S.A.', 'SARL', 'S.A.R.L.', 'S.A.S.', 'et Fils')

    siren_format = "### ### ###"

    def catch_phrase_noun(self):
        """
        Returns a random catch phrase noun.
        """
        return self.random_element(self.nouns)

    def catch_phrase_attribute(self):
        """
        Returns a random catch phrase attribute.
        """
        return self.random_element(self.attributes)

    def catch_phrase_verb(self):
        """
        Returns a random catch phrase verb.
        """
        return self.random_element(self.verbs)

    def catch_phrase(self):
        """
        :example 'integrate extensible convergence'
        """
        catch_phrase = ""
        while True:

            pattern = self.random_element(self.catch_phrase_formats)
            catch_phrase = self.generator.parse(pattern)
            catch_phrase = catch_phrase[0].upper() + catch_phrase[1:]

            if self._is_catch_phrase_valid(catch_phrase):
                break

        return catch_phrase

    # An array containing string which should not appear twice in a catch phrase
    words_which_should_not_appear_twice = ('sécurité', 'simpl')

    def _is_catch_phrase_valid(self, catch_phrase):
        """
        Validates a french catch phrase.

        :param catch_phrase: The catch phrase to validate.
        """
        for word in self.words_which_should_not_appear_twice:
            # Fastest way to check if a piece of word does not appear twice.
            begin_pos = catch_phrase.find(word)
            end_pos = catch_phrase.find(word, begin_pos + 1)

            if begin_pos != -1 and begin_pos != end_pos:
                return False

        return True

    def siren(self):
        """
        Generates a siren number (9 digits).
        """
        return self.numerify(self.siren_format)

    def siret(self, max_sequential_digits=2):
        """
        Generates a siret number (14 digits).
        It is in fact the result of the concatenation of a siren number (9 digits),
        a sequential number (4 digits) and a control number (1 digit) concatenation.
        If $max_sequential_digits is invalid, it is set to 2.
        :param max_sequential_digits The maximum number of digits for the sequential number (> 0 && <= 4).
        """
        if max_sequential_digits > 4 or max_sequential_digits <= 0:
            max_sequential_digits = 2

        sequential_number = str(self.random_number(
            max_sequential_digits)).zfill(4)
        return self.numerify(self.siren() + ' ' + sequential_number + '#')
