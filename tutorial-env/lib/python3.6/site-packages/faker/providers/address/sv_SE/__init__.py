# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):

    building_number_formats = ('###', '##', '#')

    street_name_formats = ('{{street_prefix}}{{street_suffix}}', )

    street_address_formats = ('{{street_name}} {{building_number}}',)

    street_prefixes = (
        'Björk', 'Järnvägs', 'Ring', 'Skol', 'Skogs', 'Ny', 'Gran', 'Idrotts',
        'Stor', 'Kyrk', 'Industri', 'Park', 'Strand', 'Skol', 'Trädgårds',
        'Industri', 'Ängs', 'Kyrko', 'Park', 'Villa', 'Ek', 'Kvarn', 'Stations',
        'Back', 'Furu', 'Gen', 'Fabriks', 'Åker', 'Bäck', 'Asp',
    )

    street_suffixes = ('gatan', 'gatan', 'vägen', 'vägen',
                       'stigen', 'gränd', 'torget')

    address_formats = ("{{street_address}}\n{{postcode}} {{city}}", )

    postcode_formats = ('#####', )

    city_formats = ('{{city_name}}', )

    cities = (
        'Stockholm', 'Göteborg', 'Malmö', 'Uppsala', 'Västerås', 'Örebro',
        'Linköping', 'Helsingborg', 'Jönköping', 'Norrköping', 'Lund', 'Umeå',
        'Gävle', 'Borås', 'Mölndal', 'Södertälje', 'Eskilstuna', 'Karlstad',
        'Halmstad', 'Växjö', 'Sundsvall', 'Luleå', 'Trollhättan', 'Östersund',
        'Borlänge', 'Falun', 'Kalmar', 'Skövde', 'Kristianstad', 'Karlskrona',
        'Skellefteå', 'Uddevalla', 'Lidingö', 'Motala', 'Landskrona',
        'Örnsköldsvik', 'Nyköping', 'Karlskoga', 'Varberg', 'Trelleborg',
        'Lidköping', 'Alingsås', 'Piteå', 'Sandviken', 'Ängelholm',
    )

    countries = (
        'Afghanistan', 'Albanien', 'Algeriet', 'Amerikanska Samoa', 'Andorra',
        'Angola', 'Anguilla', 'Antarktis', 'Antigua och Barbuda', 'Argentina',
        'Armenien', 'Aruba', 'Ascension', 'Australien', 'Azerbajdzjan',
        'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belgien', 'Belize',
        'Benin', 'Bermuda', 'Bhutan', 'Bolivia', 'Bosnien och Hercegovina',
        'Botswana', 'Brasilien', 'Brittiska Jungfruöarna', 'Brunei',
        'Bulgarien', 'Burkina Faso', 'Burma', 'Burundi', 'Caymanöarna',
        'Centralafrikanska republiken', 'Chile', 'Colombia', 'Cooköarna',
        'Costa Rica', 'Cypern', 'Danmark', 'Diego Garcia', 'Djibouti',
        'Dominica', 'Dominikanska republiken', 'Ecuador', 'Egypten',
        'Ekvatorialguinea', 'Elfenbenskusten', 'El Salvador', 'Eritrea',
        'Estland', 'Etiopien', 'England', 'Falklandsöarna', 'Fiji',
        'Filippinerna', 'Finland', 'Frankrike', 'Franska Guyana',
        'Franska Polynesien', 'Färöarna', 'Förenade Arabemiraten', 'Gabon',
        'Gambia', 'Georgien', 'Ghana', 'Gibraltar', 'Grekland', 'Grenada',
        'Grönland', 'Guadeloupe', 'Guatemala', 'Guinea', 'Guinea-Bissau',
        'Guyana', 'Haiti', 'Honduras', 'Hongkong', 'Indien', 'Indonesien',
        'Irak', 'Iran', 'Irland', 'Island', 'Israel', 'Italien', 'Jamaica',
        'Japan', 'Jemen', 'Jordanien', 'Kambodja', 'Kamerun', 'Kanada',
        'Kap Verde', 'Kazakstan', 'Kenya', 'Kina', 'Kirgizistan', 'Kiribati',
        'Komorerna', 'Kongo-Brazzaville', 'Kongo-Kinshasa', 'Kosovo',
        'Kroatien', 'Kuba', 'Kuwait', 'Laos', 'Lesotho', 'Lettland', 'Libanon',
        'Liberia', 'Libyen', 'Liechtenstein', 'Litauen', 'Luxemburg', 'Macao',
        'Madagaskar', 'Makedonien', 'Malawi', 'Malaysia', 'Maldiverna', 'Mali',
        'Malta', 'Marianerna', 'Marocko', 'Marshallöarna', 'Martinique',
        'Mauretanien', 'Mauritius', 'Mayotte', 'Mexiko', 'Midwayöarna',
        'Mikronesiens federerade stater', 'Moçambique', 'Moldavien', 'Monaco',
        'Mongoliet', 'Montenegro', 'Montserrat', 'Namibia', 'Nauru',
        'Nederländerna', 'Nederländska Antillerna', 'Nepal',
        'Nicaragua', 'Niger', 'Nigeria', 'Niue', 'Nordkorea', 'Nordmarianerna',
        'Norfolkön', 'Norge', 'Nya Kaledonien', 'Nya Zeeland', 'Oman',
        'Pakistan', 'Palau', 'Palestina', 'Panama', 'Papua Nya Guinea',
        'Paraguay', 'Peru', 'Pitcairnöarna', 'Polen', 'Portugal', 'Qatar',
        'Réunion', 'Rumänien', 'Rwanda', 'Ryssland', 'Saint Kitts och Nevis',
        'Saint Lucia', 'Saint-Pierre och Miquelon',
        'Saint Vincent och Grenadinerna', 'Salomonöarna', 'Samoa',
        'Sankta Helena', 'San Marino', 'São Tomé och Príncipe',
        'Saudiarabien', 'Schweiz', 'Senegal', 'Serbien', 'Seychellerna',
        'SierraLeone', 'Singapore', 'Sint Maarten', 'Slovakien', 'Slovenien',
        'Somalia', 'Spanien', 'Sri Lanka', 'Storbritannien', 'Sudan',
        'Surinam', 'Sverige', 'Swaziland', 'Sydafrika', 'Sydkorea', 'Sydsudan',
        'Syrien', 'Tadzjikistan', 'Taiwan', 'Tanzania', 'Tchad', 'Thailand',
        'Tjeckien', 'Togo', 'Tokelauöarna', 'Tonga', 'Trinidad och Tobago',
        'Tunisien', 'Turkiet', 'Turkmenistan', 'Turks-och Caicosöarna',
        'Tuvalu', 'Tyskland', 'Uganda', 'Ukraina', 'Ungern', 'Uruguay', 'USA',
        'Uzbekistan', 'Vanuatu', 'Vatikanstaten', 'Venezuela', 'Vietnam',
        'Vitryssland', 'Wake', 'Wallis-och Futunaöarna', 'Zambia', 'Zimbabwe',
        'Österrike', 'Östtimor',
    )

    states = (
        'Stockholms län', 'Uppsala län', 'Södermanlands län',
        'Östergötlands län', 'Jönköpings län', 'Kronobergs län', 'Kalmar län',
        'Gotlands län', 'Blekinge län', 'Skåne län', 'Hallands län',
        'Västra Götalands län', 'Värmlands län', 'Örebro län',
        'Västmanlands län', 'Dalarnas län', 'Gävleborgs län',
        'Västernorrlands län', 'Jämtlands län', 'Västerbottens län',
        'Norrbottens län',
    )

    def street_prefix(self):
        return self.random_element(self.street_prefixes)

    def city_name(self):
        return self.random_element(self.cities)

    def state(self):
        return self.random_element(self.states)
