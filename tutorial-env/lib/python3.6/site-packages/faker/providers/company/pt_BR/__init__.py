# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as CompanyProvider


def company_id_checksum(digits):
    digits = list(digits)
    weights = 6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2

    dv = sum(w * d for w, d in zip(weights[1:], digits))
    dv = (11 - dv) % 11
    dv = 0 if dv >= 10 else dv
    digits.append(dv)

    dv2 = sum(w * d for w, d in zip(weights, digits))
    dv2 = (11 - dv2) % 11
    dv2 = 0 if dv2 >= 10 else dv2
    digits.append(dv2)

    return digits[-2:]


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
        'a segurança',
        'o prazer',
        'o conforto',
        'a simplicidade',
        'a certeza',
        'a arte',
        'o poder',
        'o direito',
        'a possibilidade',
        'a vantagem',
        'a liberdade')

    verbs = (
        'de conseguir',
        'de avançar',
        'de evoluir',
        'de mudar',
        'de inovar',
        'de ganhar',
        'de atingir seus objetivos',
        'de concretizar seus projetos',
        'de realizar seus sonhos')

    attributes = (
        'de maneira eficaz',
        'mais rapidamente',
        'mais facilmente',
        'simplesmente',
        'com toda a tranquilidade',
        'antes de tudo',
        'naturalmente',
        'sem preocupação',
        'em estado puro',
        'com força total',
        'direto da fonte',
        'com confiança')

    company_suffixes = ('S/A', 'S.A.', 'Ltda.', '- ME', '- EI', 'e Filhos')

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
        :example 'a segurança de evoluir sem preocupação'
        """
        pattern = self.random_element(self.catch_phrase_formats)
        catch_phrase = self.generator.parse(pattern)
        catch_phrase = catch_phrase[0].upper() + catch_phrase[1:]
        return catch_phrase

    def company_id(self):
        digits = self.random_sample(range(10), 8) + [0, 0, 0, 1]
        digits += company_id_checksum(digits)
        return ''.join(str(d) for d in digits)

    def cnpj(self):
        digits = self.company_id()
        return '{}.{}.{}/{}-{}'.format(digits[:2], digits[2:5], digits[5:8],
                                       digits[8:12], digits[12:])
