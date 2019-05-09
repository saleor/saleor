# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):
    building_number_formats = ('###', '##', '#')

    postcode_formats = ('#####', )

    city_formats = ('{{city_name}}', )

    street_name_formats = ('{{street_prefix}}{{street_suffix}}', )

    street_address_formats = ('{{street_name}} {{building_number}}', )

    address_formats = ("{{street_address}}\n{{postcode}} {{city}}", )

    # Data from:
    # https://www.avoindata.fi/data/en/dataset/kunnat/resource/b1cb9870-191f-4616-9c53-5388b7ca6beb
    cities = (
        'Alajärvi', 'Alavieska', 'Alavus', 'Asikkala', 'Askola', 'Aura', 'Akaa', 'Brändö', 'Eckerö', 'Enonkoski',
        'Enontekiö', 'Espoo', 'Eura', 'Eurajoki', 'Evijärvi', 'Finström', 'Forssa', 'Föglö', 'Geta', 'Haapajärvi',
        'Haapavesi', 'Hailuoto', 'Halsua', 'Hamina', 'Hammarland', 'Hankasalmi', 'Hanko', 'Harjavalta', 'Hartola',
        'Hattula', 'Hausjärvi', 'Heinävesi', 'Helsinki', 'Vantaa', 'Hirvensalmi', 'Hollola', 'Honkajoki', 'Huittinen',
        'Humppila', 'Hyrynsalmi', 'Hyvinkää', 'Hämeenkyrö', 'Hämeenlinna', 'Heinola', 'Ii', 'Iisalmi', 'Iitti',
        'Ikaalinen', 'Ilmajoki', 'Ilomantsi', 'Inari', 'Inkoo', 'Isojoki', 'Isokyrö', 'Imatra', 'Janakkala', 'Joensuu',
        'Jokioinen', 'Jomala', 'Joroinen', 'Joutsa', 'Juuka', 'Juupajoki', 'Juva', 'Jyväskylä', 'Jämijärvi', 'Jämsä',
        'Järvenpää', 'Kaarina', 'Kaavi', 'Kajaani', 'Kalajoki', 'Kangasala', 'Kangasniemi', 'Kankaanpää', 'Kannonkoski',
        'Kannus', 'Karijoki', 'Karkkila', 'Karstula', 'Karvia', 'Kaskinen', 'Kauhajoki', 'Kauhava', 'Kauniainen',
        'Kaustinen', 'Keitele', 'Kemi', 'Keminmaa', 'Kempele', 'Kerava', 'Keuruu', 'Kihniö', 'Kinnula', 'Kirkkonummi',
        'Kitee', 'Kittilä', 'Kiuruvesi', 'Kivijärvi', 'Kokemäki', 'Kokkola', 'Kolari', 'Konnevesi', 'Kontiolahti',
        'Korsnäs', 'Koski Tl', 'Kotka', 'Kouvola', 'Kristiinankaupunki', 'Kruunupyy', 'Kuhmo', 'Kuhmoinen', 'Kumlinge',
        'Kuopio', 'Kuortane', 'Kurikka', 'Kustavi', 'Kuusamo', 'Outokumpu', 'Kyyjärvi', 'Kärkölä', 'Kärsämäki', 'Kökar',
        'Kemijärvi', 'Kemiönsaari', 'Lahti', 'Laihia', 'Laitila', 'Lapinlahti', 'Lappajärvi', 'Lappeenranta',
        'Lapinjärvi', 'Lapua', 'Laukaa', 'Lemi', 'Lemland', 'Lempäälä', 'Leppävirta', 'Lestijärvi', 'Lieksa', 'Lieto',
        'Liminka', 'Liperi', 'Loimaa', 'Loppi', 'Loviisa', 'Luhanka', 'Lumijoki', 'Lumparland', 'Luoto', 'Luumäki',
        'Lohja', 'Parainen', 'Maalahti', 'Maarianhamina', 'Marttila', 'Masku', 'Merijärvi', 'Merikarvia', 'Miehikkälä',
        'Mikkeli', 'Muhos', 'Multia', 'Muonio', 'Mustasaari', 'Muurame', 'Mynämäki', 'Myrskylä', 'Mäntsälä',
        'Mäntyharju', 'Mänttä-Vilppula', 'Naantali', 'Nakkila', 'Nivala', 'Nokia', 'Nousiainen', 'Nurmes', 'Nurmijärvi',
        'Närpiö', 'Orimattila', 'Oripää', 'Orivesi', 'Oulainen', 'Oulu', 'Padasjoki', 'Paimio', 'Paltamo', 'Parikkala',
        'Parkano', 'Pelkosenniemi', 'Perho', 'Pertunmaa', 'Petäjävesi', 'Pieksämäki', 'Pielavesi', 'Pietarsaari',
        'Pedersören kunta', 'Pihtipudas', 'Pirkkala', 'Polvijärvi', 'Pomarkku', 'Pori', 'Pornainen', 'Posio',
        'Pudasjärvi', 'Pukkila', 'Punkalaidun', 'Puolanka', 'Puumala', 'Pyhtää', 'Pyhäjoki', 'Pyhäjärvi', 'Pyhäntä',
        'Pyhäranta', 'Pälkäne', 'Pöytyä', 'Porvoo', 'Raahe', 'Raisio', 'Rantasalmi', 'Ranua', 'Rauma', 'Rautalampi',
        'Rautavaara', 'Rautjärvi', 'Reisjärvi', 'Riihimäki', 'Ristijärvi', 'Rovaniemi', 'Ruokolahti', 'Ruovesi',
        'Rusko', 'Rääkkylä', 'Raasepori', 'Saarijärvi', 'Salla', 'Salo', 'Saltvik', 'Sauvo', 'Savitaipale',
        'Savonlinna', 'Savukoski', 'Seinäjoki', 'Sievi', 'Siikainen', 'Siikajoki', 'Siilinjärvi', 'Simo', 'Sipoo',
        'Siuntio', 'Sodankylä', 'Soini', 'Somero', 'Sonkajärvi', 'Sotkamo', 'Sottunga', 'Sulkava', 'Sund',
        'Suomussalmi', 'Suonenjoki', 'Sysmä', 'Säkylä', 'Vaala', 'Sastamala', 'Siikalatva', 'Taipalsaari',
        'Taivalkoski', 'Taivassalo', 'Tammela', 'Tampere', 'Tervo', 'Tervola', 'Teuva', 'Tohmajärvi', 'Toholampi',
        'Toivakka', 'Tornio', 'Turku', 'Pello', 'Tuusniemi', 'Tuusula', 'Tyrnävä', 'Ulvila', 'Urjala', 'Utajärvi',
        'Utsjoki', 'Uurainen', 'Uusikaarlepyy', 'Uusikaupunki', 'Vaasa', 'Valkeakoski', 'Valtimo', 'Varkaus', 'Vehmaa',
        'Vesanto', 'Vesilahti', 'Veteli', 'Vieremä', 'Vihti', 'Viitasaari', 'Vimpeli', 'Virolahti', 'Virrat', 'Värdö',
        'Vöyri', 'Ylitornio', 'Ylivieska', 'Ylöjärvi', 'Ypäjä', 'Ähtäri', 'Äänekoski',
    )

    countries = (
        'Afganistan', 'Alankomaat', 'Albania', 'Algeria', 'Andorra', 'Angola',
        'Antigua ja Barbuda', 'Argentiina', 'Armenia', 'Australia',
        'Azerbaidžan', 'Bahama', 'Bahrain', 'Bangladesh', 'Barbados', 'Belgia',
        'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia ja Hertsegovina',
        'Botswana', 'Brasilia', 'Brunei', 'Bulgaria', 'Burkina', 'Faso',
        'Burundi', 'Chile', 'Costa', 'Rica', 'Djibouti', 'Dominica',
        'Dominikaaninen tasavalta', 'Ecuador', 'Egypti', 'El', 'Salvador',
        'Eritrea', 'Espanja', 'Etelä-Afrikka', 'Korean tasavalta',
        'Etelä-Sudan', 'Etiopia', 'Fidži', 'Filippiinit', 'Gabon', 'Gambia',
        'Georgia', 'Ghana', 'Grenada', 'Guatemala', 'Guinea-Bissau', 'Guinea',
        'Guyana', 'Haiti', 'Honduras', 'Indonesia', 'Intia', 'Irak', 'Iran',
        'Irlanti', 'Islanti', 'Israel', 'Italia', 'Itä-Timor', 'Itävalta',
        'Jamaika', 'Japani', 'Jemen', 'Jordania', 'Kambodža', 'Kamerun',
        'Kanada', 'Kap', 'Verde', 'Kazakstan', 'Kenia',
        'Keski-Afrikan tasavalta', 'Kiina', 'Kirgisia', 'Kiribati',
        'Kolumbia', 'Komorit', 'Kongon demokraattinen tasavalta',
        'Kongon tasavalta', 'Kosovo', 'Kreikka', 'Kroatia', 'Kuuba', 'Kuwait',
        'Kypros', 'Laos', 'Latvia', 'Lesotho', 'Libanon', 'Liberia', 'Libya',
        'Liechtenstein', 'Liettua', 'Luxemburg', 'Madagaskar', 'Makedonia',
        'Malawi', 'Malediivit', 'Malesia', 'Mali', 'Malta', 'Marokko',
        'Marshallinsaaret', 'Mauritania', 'Mauritius', 'Meksiko', 'Mikronesia',
        'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Mosambik', 'Myanmar',
        'Namibia', 'Nauru', 'Nepal', 'Nicaragua', 'Nigeria', 'Niger', 'Norja',
        'Norsunluurannikko', 'Oman', 'Pakistan', 'Palau', 'Panama',
        'Papua-Uusi-Guinea', 'Paraguay', 'Peru',
        'Korean demokraattinen kansantasavalta', 'Portugali', 'Puola',
        'Päiväntasaajan Guinea', 'Qatar', 'Ranska', 'Romania', 'Ruanda',
        'Ruotsi', 'Saint Kitts ja Nevis', 'Saint Lucia',
        'Saint Vincent ja Grenadiinit', 'Saksa', 'Salomonsaaret', 'Sambia',
        'Samoa', 'San Marino', 'São Tomé ja Príncipe',
        'Saudi-Arabia', 'Senegal', 'Serbia', 'Seychellit', 'Sierra', 'Leone',
        'Singapore', 'Slovakia', 'Slovenia', 'Somalia', 'Sri', 'Lanka', 'Sudan',
        'Suomi', 'Suriname', 'Swazimaa', 'Sveitsi', 'Syyria', 'Tadžikistan',
        'Tansania', 'Tanska', 'Thaimaa', 'Togo', 'Tonga', 'Trinidad ja Tobago',
        'Tšad', 'Tšekki', 'Tunisia', 'Turkki', 'Turkmenistan', 'Tuvalu',
        'Uganda', 'Ukraina', 'Unkari', 'Uruguay', 'Uusi-Seelanti', 'Uzbekistan',
        'Valko-Venäjä', 'Vanuatu', 'Vatikaanivaltio', 'Venezuela', 'Venäjä',
        'Vietnam', 'Viro', 'Yhdistyneet arabiemiirikunnat',
        'Yhdistynyt kuningaskunta', 'Yhdysvallat', 'Zimbabwe',
    )

    states = (
        'Turun ja Porin lääni', 'Uudenmaan ja Hämeen lääni', 'Pohjanmaan lääni',
        'Viipurin ja Savonlinnan lääni', 'Käkisalmen lääni',
        'Savonlinnan ja Kymenkartanon lääni', 'Kymenkartanon ja Savon lääni',
        'Vaasan lääni', 'Oulun lääni', 'Kymenkartanon lääni',
        'Savon ja Karjalan lääni', 'Viipurin lääni', 'Uudenmaan lääni',
        'Hämeen lääni', 'Mikkelin lääni', 'Kuopion lääni', 'Ahvenanmaan lääni',
        'Petsamon lääni', 'Lapin lääni', 'Kymen lääni', 'Keski-Suomen lääni',
        'Pohjois-Karjalan lääni', 'Etelä-Suomen lääni', 'Länsi-Suomen lääni',
        'Itä-Suomen lääni', '', 'Turun ja Porin lääni',
        'Uudenmaan ja Hämeen lääni', 'Pohjanmaan lääni',
        'Viipurin ja Savonlinnan lääni', 'Käkisalmen lääni',
        'Savonlinnan ja Kymenkartanon lääni', 'Kymenkartanon ja Savon lääni',
        'Vaasan lääni', 'Oulun lääni', 'Kymenkartanon lääni',
        'Savon ja Karjalan lääni', 'Viipurin lääni', 'Uudenmaan lääni',
        'Hämeen lääni', 'Mikkelin lääni', 'Kuopion lääni', 'Ahvenanmaan lääni',
        'Petsamon lääni', 'Lapin lääni', 'Kymen lääni', 'Keski-Suomen lääni',
        'Pohjois-Karjalan lääni', 'Etelä-Suomen lääni', 'Länsi-Suomen lääni',
        'Itä-Suomen lääni',
    )

    street_suffixes = ('tie', 'katu', 'polku', 'kuja', 'bulevardi')

    # Prefixes parsed from a street list of Helsinki:
    # http://kartta.hel.fi/ws/geoserver/avoindata/wfs?outputFormat=application/json&REQUEST=GetFeature&typeNames=avoindata:Helsinki_osoiteluettelo

    street_prefixes = (
        'Adolf Lindforsin ', 'Agnes Sjöbergin ', 'Agnetan', 'Agricolan', 'Ahomäen', 'Ahvenkosken', 'Aidasmäen',
        'Agroksen', 'Agronomin', 'Ahdekaunokin', 'Bertel Jungin ', 'Bertha Pauligin ', 'Betlehemin', 'Betoni',
        'Biologin', 'Birger Kaipiaisen ', 'Bysantin', 'Böstaksen', 'Bengalin', 'Benktan', 'Bergan', 'Caloniuksen',
        'Capellan puisto', 'Castrénin', 'Chydeniuksen', 'Cygnaeuksen', 'Dagmarin', 'Damaskuksen', 'Degermosan', 'Disan',
        'Dosentin', 'Dunckerin', 'Döbelnin', 'Ehrensvärdin', 'Eino Leinon ', 'Elimäen', 'Elisabeth Kochin ', 'Eljaksen',
        'Elon', 'Elon', 'Edelfeltin', 'Eduskunta', 'Eerik Pyhän ', 'Franzénin', 'Fredrikin', 'Freesen',
        'Fabianin', 'Fagotti', 'Fahlanderin puisto', 'Fallin', 'Fallkullan', 'Fallpakan', 'Fastbölen', 'Gadolinin',
        'Gneissi', 'Granfeltin', 'Gunillan', 'Gunnel Nymanin ', 'Graniitti', 'Gustav Pauligin ', 'Gyldénin',
        'Gotlannin', 'Haapa', 'Haagan pappilan', 'Haahka', 'Haakoninlahden', 'Haaksi', 'Hankasuon', 'Hannukselan',
        'Harakkamyllyn', 'Harava', 'Harbon', 'Ilmattaren', 'Ilomäen', 'Ilotulitus', 'Iltaruskon', 'Iltatähden', 'Ilves',
        'Immolan', 'Ilkan', 'Ida Ekmanin ', 'Ies', 'Jälsi', 'Jämsän', 'Jänkä', 'Jänne', 'Järkäle', 'Jätkäsaaren',
        'Jättiläisen', 'Jyvä', 'Jägerhornin', 'Jäkälä', 'Kukkaniityn', 'Kolsin', 'Kolu', 'Kolvi', 'Kuhankeittäjän',
        'Katajaharjun', 'Kiitäjän', 'Kilpolan', 'Kimalais', 'Kimmon', 'Laajasalon', 'Laakavuoren', 'Lemun',
        'Lentokapteenin ', 'Lepolan', 'Louhen', 'Louhikko', 'Lukkarimäen', 'Laurinniityn', 'Lautamiehen',
        'Mamsellimyllyn', 'Mannerheimin', 'Maanmittarin', 'Maapadon', 'Maa', 'Maasalon', 'Maasälvän', 'Maatullin',
        'Malminkartanon', 'Maneesi', 'Niittylän', 'Niemi', 'Niitynperän', 'Nikon', 'Nils Westermarckin ',
        'Nordenskiöldin', 'Nelikko', 'Neon', 'Nervanderin', 'Neulapadon', 'Ostos', 'Orapihlaja', 'Oras', 'Orava',
        'Osmon', 'Osuuskunnan', 'Orisaaren', 'Ormus', 'Orvokki', 'Oterman', 'Pore', 'Porin', 'Porkkalan', 'Pyörökiven',
        'Puusepän', 'Puuska', 'Pohjolan', 'Poikasaarten', 'Purjetuulen', 'Puroniityn', 'Rukkilan', 'Ruko',
        'Rukoushuoneen', 'Runebergin', 'Runoilijan', 'Runokylän', 'Runonlaulajan', 'Rantavaraston', 'Rapakiven',
        'Rapolan', 'Santerlan', 'Saparon', 'Sapilas', 'Saramäen', 'Saanatunturin', 'Sade', 'Sahaajan', 'Salakka',
        'Salama', 'Salava', 'Tuomarinkylän', 'Tuulilasin', 'Taavetti Laitisen ', 'Taavin', 'Tahti', 'Taimiston',
        'Tukkisillan', 'Tuohikoivun', 'Tyynelän', 'Tyynylaavan', 'Uussillan', 'Urheilu', 'Urkurin', 'Urpu', 'Uskalikon',
        'Usva', 'Uudenkaupungin', 'Uunilinnun', 'Uunisepän', 'Uurtajan', 'Vanha Raja', 'Veropellon', 'Veräjämäen',
        'Vesakko', 'Vesalan', 'Vellikellon', 'Verkko', 'Verso', 'Vaakalinnun', 'Vaarna', 'Wavulinin',
        'Walentin Chorellin ', 'Wallinin', 'Waseniuksen puisto', 'Wecksellin', 'Willebrandin', 'Winqvistin',
        'Wäinö Aaltosen ', 'Werner Wirénin ', 'Yhteiskoulun', 'Ylipalon', 'Yllästunturin', 'Ylä-Fallin ', 'Yläkasken',
        'Ylänkö', 'Ylätuvan', 'Yrjö-Koskisen ', 'Yrjön', 'Yrttimaan', 'Zaidan',
    )

    def street_prefix(self):
        return self.random_element(self.street_prefixes)

    def city_name(self):
        return self.random_element(self.cities)

    def state(self):
        return self.random_element(self.states)
