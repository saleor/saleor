# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):
    city_suffixes = ('-des-Bois', '-les-Bains', '-la-Ville', '-Dessus',
                     '-Dessous', ' am Rhein', ' am See', ' am Albis',
                     ' an der Aare')
    city_prefixes = ('Saint ', 'Sainte ', 'San ', 'Ober', 'Unter')
    street_prefixes = ('rue', 'rue', 'chemin', 'avenue', 'boulevard')

    address_formats = ("{{street_address}}\n{{postcode}} {{city}}", )

    building_number_formats = ('%', '%#', '%#', '%#', '%##')

    city_formats = ('{{last_name}}', '{{last_name}}', '{{last_name}}',
                    '{{last_name}}', '{{last_name}}{{city_suffix}}',
                    '{{last_name}}{{city_suffix}}',
                    '{{last_name}}{{city_suffix}}',
                    '{{last_name}}-près-{{last_name}}',
                    '{{last_name}}-sur-{{last_name}}',
                    '{{city_prefix}}{{last_name}}',
                    '{{last_name}} ({{canton_code}})')

    street_address_formats = ('{{street_name}}',
                              '{{street_name}} {{building_number}}',
                              '{{street_name}} {{building_number}}',
                              '{{street_name}} {{building_number}}',
                              '{{street_name}} {{building_number}}',
                              '{{street_name}} {{building_number}}')
    street_name_formats = ('{{street_prefix}} {{last_name}}',
                           '{{street_prefix}} {{first_name}} {{last_name}}',
                           '{{street_prefix}} de {{last_name}}')

    postcode_formats = ('1###', '2###', '3###', '4###', '5###', '6###', '7###',
                        '8###', '9###')

    cantons = (('AG', 'Argovie'), ('AI', 'Appenzell Rhodes-Intérieures'),
               ('AR', 'Appenzell Rhodes-Extérieures'), ('BE', 'Berne'),
               ('BL', 'Bâle-Campagne'), ('BS', 'Bâle-Ville'), ('FR', 'Fribourg'),
               ('GE', 'Genève'), ('GL', 'Glaris'), ('GR', 'Grisons'), ('JU', 'Jura'),
               ('LU', 'Lucerne'), ('NE', 'Neuchâtel'), ('NW', 'Nidwald'), ('OW', 'Obwald'),
               ('SG', 'Saint-Gall'), ('SH', 'Schaffhouse'), ('SO', 'Soleure'),
               ('SZ', 'Schwytz'), ('TG', 'Thurgovie'), ('TI', 'Tessin'), ('UR', 'Uri'),
               ('VD', 'Vaud'), ('VS', 'Valais'), ('ZG', 'Zoug'), ('ZH', 'Zurich'))

    countries = (
        'Afghanistan', 'Afrique du sud', 'Albanie', 'Algérie', 'Allemagne',
        'Andorre', 'Angola', 'Anguilla', 'Antarctique', 'Antigua et Barbuda',
        'Antilles néerlandaises', 'Arabie saoudite', 'Argentine', 'Arménie',
        'Aruba', 'Australie', 'Autriche', 'Azerbaïdjan', 'Bahamas', 'Bahrain',
        'Bangladesh', 'Belgique', 'Belize', 'Benin', 'Bermudes (Les)',
        'Bhoutan', 'Biélorussie', 'Bolivie', 'Bosnie-Herzégovine', 'Botswana',
        'Bouvet (Îles)', 'Brunei', 'Brésil', 'Bulgarie', 'Burkina Faso',
        'Burundi', 'Cambodge', 'Cameroun', 'Canada', 'Cap Vert',
        'Cayman (Îles)', 'Chili', 'Chine (Rép. pop.)', 'Christmas (Île)',
        'Chypre', 'Cocos (Îles)', 'Colombie', 'Comores', 'Cook (Îles)',
        'Corée du Nord', 'Corée, Sud', 'Costa Rica', 'Croatie', 'Cuba',
        'Côte d\'Ivoire', 'Danemark', 'Djibouti', 'Dominique', 'Égypte',
        'El Salvador', 'Émirats arabes unis', 'Équateur', 'Érythrée',
        'Espagne', 'Estonie', 'États-Unis', 'Ethiopie', 'Falkland (Île)',
        'Fidji (République des)', 'Finlande', 'France',
        'Féroé (Îles)', 'Gabon', 'Gambie', 'Ghana', 'Gibraltar', 'Grenade',
        'Groenland', 'Grèce', 'Guadeloupe', 'Guam', 'Guatemala', 'Guinée',
        'Guinée Equatoriale', 'Guinée-Bissau', 'Guyane', 'Guyane française',
        'Géorgie', 'Géorgie du Sud et Sandwich du Sud (Îles)', 'Haïti',
        'Heard et McDonald (Îles)', 'Honduras', 'Hong Kong', 'Hongrie',
        'Îles Mineures Éloignées des États-Unis', 'Inde', 'Indonésie', 'Irak',
        'Iran', 'Irlande', 'Islande', 'Israël', 'Italie', 'Jamaïque', 'Japon',
        'Jordanie', 'Kazakhstan', 'Kenya', 'Kirghizistan', 'Kiribati',
        'Koweit', 'La Barbad', 'Laos', 'Lesotho', 'Lettonie', 'Liban', 'Libye',
        'Libéria', 'Liechtenstein', 'Lithuanie', 'Luxembourg', 'Macau',
        'Macédoine', 'Madagascar', 'Malaisie', 'Malawi', 'Maldives (Îles)',
        'Mali', 'Malte', 'Mariannes du Nord (Îles)', 'Maroc',
        'Marshall (Îles)', 'Martinique', 'Maurice', 'Mauritanie', 'Mayotte',
        'Mexique', 'Micronésie (États fédérés de)', 'Moldavie', 'Monaco',
        'Mongolie', 'Montserrat', 'Mozambique', 'Myanmar', 'Namibie', 'Nauru',
        'Nepal', 'Nicaragua', 'Niger', 'Nigeria', 'Niue', 'Norfolk (Îles)',
        'Norvège', 'Nouvelle Calédonie', 'Nouvelle-Zélande', 'Oman', 'Ouganda',
        'Ouzbékistan', 'Pakistan', 'Palau', 'Panama',
        'Papouasie-Nouvelle-Guinée', 'Paraguay', 'Pays-Bas', 'Philippines',
        'Pitcairn (Îles)', 'Pologne', 'Polynésie française', 'Porto Rico',
        'Portugal', 'Pérou', 'Qatar', 'Roumanie', 'Royaume-Uni', 'Russie',
        'Rwanda', 'Rép. Dém. du Congo', 'République centrafricaine',
        'République Dominicaine', 'République tchèque', 'Réunion (La)',
        'Sahara Occidental', 'Saint Pierre et Miquelon',
        'Saint Vincent et les Grenadines', 'Saint-Kitts et Nevis',
        'Saint-Marin (Rép. de)', 'Sainte Hélène', 'Sainte Lucie', 'Samoa',
        'Samoa', 'Seychelles', 'Sierra Leone', 'Singapour', 'Slovaquie',
        'Slovénie', 'Somalie', 'Soudan', 'Sri Lanka', 'Suisse', 'Suriname',
        'Suède', 'Svalbard et Jan Mayen (Îles)', 'Swaziland', 'Syrie',
        'São Tomé et Príncipe (Rép.)', 'Sénégal', 'Tadjikistan', 'Taiwan',
        'Tanzanie', 'Tchad', 'Territoire britannique de l\'océan Indien',
        'Territoires français du sud', 'Thailande', 'Timor', 'Togo', 'Tokelau',
        'Tonga', 'Trinité et Tobago', 'Tunisie', 'Turkménistan',
        'Turks et Caïques (Îles)', 'Turquie', 'Tuvalu', 'Ukraine', 'Uruguay',
        'Vanuatu', 'Vatican (Etat du)', 'Venezuela', 'Vierges (Îles)',
        'Vierges britanniques (Îles)', 'Vietnam', 'Wallis et Futuna (Îles)',
        'Yemen', 'Yougoslavie', 'Zambie', 'Zaïre', 'Zimbabwe')

    def street_prefix(self):
        """
        :example 'rue'
        """
        return self.random_element(self.street_prefixes)

    def city_prefix(self):
        """
        :example 'rue'
        """
        return self.random_element(self.city_prefixes)

    def canton(self):
        """
        Randomly returns a swiss canton ('Abbreviated' , 'Name').
        :example ('VD' . 'Vaud')
        """
        return self.random_element(self.cantons)

    def canton_name(self):
        """
        Randomly returns a Swiss canton name.
        :example 'Vaud'
        """
        return self.canton()[1]

    def canton_code(self):
        """
        Randomly returns a Swiss canton code.
        :example 'VD'
        """
        return self.canton()[0]
