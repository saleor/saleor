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
        'a segurança', 'o prazer', 'o conforto', 'a simplicidade', 'a certeza',
        'a arte', 'o poder', 'o direito', 'a possibilidade', 'a vantagem',
        'a liberdade',
    )

    verbs = (
        'de conseguir', 'de avançar', 'de evoluir', 'de mudar', 'de inovar',
        'de ganhar', 'de atingir os seus objetivos',
        'de concretizar seus projetos', 'de realizar seus sonhos',
    )

    attributes = (
        'de maneira eficaz', 'mais rapidamente', 'mais facilmente',
        'simplesmente', 'com toda a tranquilidade', 'antes de tudo',
        'naturalmente', 'sem preocupação', 'em estado puro', 'com força total',
        'direto da fonte', 'com confiança',
    )

    company_suffixes = ('S/A', 'S.A.', 'Lda.', 'e Filhos')
