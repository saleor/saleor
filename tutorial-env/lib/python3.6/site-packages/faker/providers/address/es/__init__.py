# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):

    # List of Countries https://www.un.org/es/members/
    countries = (
        'Afganistán', 'Albania', 'Alemania', 'Andorra', 'Angola',
        'Antigua y Barbuda', 'Arabia Saudita', 'Argelia', 'Argentina',
        'Armenia', 'Australia', 'Austria', 'Azerbaiyán', 'Bahamas', 'Bahrein',
        'Bangladesh', 'Barbados', 'Belarús', 'Bélgica', 'Belice', 'Benin',
        'Bhután', 'Bolivia', 'Bosnia y Herzegovina', 'Botswana', 'Brasil',
        'Brunei Darussalam', 'Bulgaria', 'Burkina Faso', 'Burundi',
        'Cabo Verde', 'Camboya', 'Camerún', 'Canadá', 'Chad', 'Chile', 'China',
        'Chipre', 'Colombia', 'Comoras', 'Congo', 'Costa Rica',
        'Côte d\'Ivoire', 'Croacia', 'Cuba', 'Dinamarca', 'Djibouti',
        'Dominicana', 'Ecuador', 'Egipto', 'El Salvador',
        'Emiratos Árabes Unidos', 'Eritrea', 'Eslovaquia', 'Eslovenia',
        'España', 'Estados Unidos de América', 'Estonia', 'Etiopía',
        'ex República Yugoslava de Macedonia', 'Federación de Rusia', 'Fiji',
        'Filipinas', 'Finlandia', 'Francia', 'Gabón', 'Gambia', 'Georgia',
        'Ghana', 'Granada', 'Grecia', 'Guatemala', 'Guinea', 'Guinea Bissau',
        'Guinea Ecuatorial', 'Guyana', 'Haití', 'Honduras', 'Hungría', 'India',
        'Indonesia', 'Irán', 'Iraq', 'Irlanda', 'Islandia', 'Islas Marshall',
        'Islas Salomón', 'Israel', 'Italia', 'Jamaica', 'Japón', 'Jordania',
        'Kazajstán', 'Kenya', 'Kirguistán', 'Kiribati', 'Kuwait', 'Lesotho',
        'Letonia', 'Líbano', 'Liberia', 'Libia', 'Liechtenstein', 'Lituania',
        'Luxemburgo', 'Madagascar', 'Malasia', 'Malawi', 'Maldivas', 'Mali',
        'Malta', 'Marruecos', 'Mauricio', 'Mauritania', 'México', 'Micronesia',
        'Mónaco', 'Mongolia', 'Montenegro', 'Mozambique', 'Myanmar', 'Namibia',
        'Nauru', 'Nicaragua', 'Niger', 'Nigeria', 'Noruega', 'Nueva Zelandia',
        'Omán', 'Países Bajos', 'Pakistán', 'Palau', 'Panamá',
        'Papua Nueva Guinea', 'Paraguay', 'Perú', 'Polonia', 'Portugal',
        'Qatar', 'Reino Unido de Gran Bretaña e Irlanda del Norte',
        'República Árabe Siria', 'República Centroafricana', 'República Checa',
        'República de Corea', 'República de Moldova',
        'República Democrática del Congo', 'República Democrática Popular Lao',
        'República Dominicana', 'República Federal Democrática de Nepal',
        'República Popular Democrática de Corea', 'República Unida de Tanzanía',
        'Rumania', 'Rwanda', 'Saint Kitts y Nevis', 'Samoa', 'San Marino',
        'Santa Lucía', 'Santo Tomé y Príncipe', 'San Vicente y las Granadinas',
        'Senegal', 'Serbia', 'Seychelles', 'Sierra Leona', 'Singapur',
        'Somalia', 'Sri Lanka', 'Sudáfrica', 'Sudán', 'Sudán del Sur', 'Suecia',
        'Suiza', 'Suriname', 'Swazilandia', 'Tailandia', 'Tayikistán',
        'Timor-Leste', 'Togo', 'Tonga', 'Trinidad y Tabago', 'Túnez',
        'Turkmenistán', 'Turquía', 'Tuvalu', 'Ucrania', 'Uganda', 'Uruguay',
        'Uzbekistán', 'Vanuatu', 'Venezuela', 'Vietman', 'Yemen', 'Zambia',
        'Zimbabwe',
    )
