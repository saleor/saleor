# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):

    city_formats = ('{{city_name}}', )

    street_name_formats = ('{{street_name}}', )
    street_address_formats = ('{{street_name}} {{building_number}}', )
    address_formats = ('{{street_address}}\n{{postcode}} {{city}}', )

    building_number_formats = ('###', '##', '#', '#a', '#b', '#c',
                               '#a/#', '#b/#', '#c/#')

    postcode_formats = ('#####', )

    street_suffixes_long = (
        '', 'ulica', 'cesta', 'put', 'avenija',
    )
    street_suffixes_short = (
        '', 'ul.', 'c.', 'a.',
    )

    cities = (
        "Bakar", "Beli Manastir", "Belišće", "Benkovac", "Biograd na Moru",
        "Bjelovar", "Buje", "Buzet", "Cres", "Crikvenica", "Čabar", "Čakovec",
        "Čazma", "Daruvar", "Delnice", "Donja Stubica", "Donji Miholjac",
        "Drniš", "Dubrovnik", "Duga Resa", "Dugo Selo", "Đakovo", "Đurđevac",
        "Garešnica", "Glina", "Gospić", "Grubišno Polje",
        "Hrvatska Kostajnica", "Hvar", "Ilok", "Imotski", "Ivanec",
        "Ivanić-Grad", "Jastrebarsko", "Karlovac", "Kastav", "Kaštela",
        "Klanjec", "Knin", "Komiža", "Koprivnica", "Korčula", "Kraljevica",
        "Krapina", "Križevci", "Krk", "Kutina", "Kutjevo", "Labin",
        "Lepoglava", "Lipik", "Ludbreg", "Makarska", "Mali Lošinj",
        "Metković", "Mursko Središće", "Našice", "Nin", "Nova Gradiška",
        "Novalja", "Novi Marof", "Novi Vinodolski", "Novigrad", "Novska",
        "Obrovac", "Ogulin", "Omiš", "Opatija", "Opuzen", "Orahovica",
        "Oroslavje", "Osijek", "Otočac", "Otok", "Ozalj", "Pag", "Pakrac",
        "Pazin", "Petrinja", "Pleternica", "Ploče", "Popovača", "Poreč",
        "Požega", "Pregrada", "Prelog", "Pula", "Rab", "Rijeka", "Rovinj",
        "Samobor", "Senj", "Sinj", "Sisak", "Skradin", "Slatina",
        "Slavonski Brod", "Slunj", "Solin", "Split", "Stari Grad",
        "Supetar", "Sveta Nedelja", "Sveti Ivan Zelina", "Šibenik",
        "Trilj", "Trogir", "Umag", "Valpovo", "Varaždin",
        "Varaždinske Toplice", "Velika Gorica", "Vinkovci", "Virovitica",
        "Vis", "Vodice", "Vodnjan", "Vrbovec", "Vrbovsko", "Vrgorac",
        "Vrlika", "Vukovar", "Zabok", "Zadar", "Zagreb", "Zaprešić", "Zlatar",
    )

    streets = (
        "Arnoldova", "Bakačeva", "Bijenička", "Bosanska", "Bučarova",
        "Cmrok", "Čačkovićeva", "Davor", "Demetrova",
        "Dolac", "Donje Prekrižje", "Draškovićeva", "Dubravkin",
        "Dverce", "Dvoranski prečac", "Glogovac", "Golubovac", "Goljačke",
        "Goljak", "Gornje Prekrižje", "Gračanska", "Gradec", "Grič",
        "Gupčeva zvijezda", "Harmica", "Hercegovačka", "Horvatovac",
        "Ilica", "Istarska", "Jabukovac", "Jadranska", "Jagodnjak",
        "Javorovac", "Jezuitski trg", "Jurišićeva", "Jurjeve",
        "Jurjevska", "Jurkovićeva", "Kamaufova", "Kamenita", "Kamenjak",
        "Kaptol", "Kapucinske", "Klanac Grgura Tepečića", "Klenovac",
        "Klesarski put", "Kozarčev vijenac", "Kožarska", "Kraljevec",
        "Kraljevec II.", "Kraljevečki odvojak", "Kraljevečki ogranak",
        "Krležin gvozd", "Krvavi most", "Ksaver", "Ksaverska", "Kurelčeva",
        "Lisinskoga", "Lobmayerove", "Ljubinkovac", "Magdićeve", "Mala",
        "Male", "Mašekova", "Medvedgradska", "Medveščak", "Mesnička",
        "Mihaljevac", "Mirogojska", "Mletačka", "Mlinarska", "Mlinovi",
        "Mlinske", "Naumovac", "Nemetova", "Nova Ves",
        "Novi Goljak", "Opatička", "Opatovina", "Orlovac",
        "Palmotićeva", "Pantovčak", "Paunovac",
        "Perivoj biskupa Stjepana II.", "Perivoj srpanjskih žrtava",
        "Petrova", "Pod zidom", "Podgaj", "Radnički dol", "Remetska",
        "Ribnjak", "Rikardove", "Rockefellerova", "Rokov perivoj", "Rokova",
        "Ružičnjak", "Skalinska", "Slavujevac", "Splavnica",
        "Srebrnjak", "Streljačka", "Strossmayerovo šetalište", "Svibovac",
        "Svibovac", "Šalata", "Šestinski vijenac", "Šestinski vrh",
        "Šilobodov put", "Šumski prečac", "Tkalčićeva", "Tošovac",
        "Tuškanac", "Vijenac", "Vinogradska", "Visoka", "Višnjica",
        "Višnjičke", "Vitezovićeva", "Vlaška", "Voćarska", "Voćarsko naselje",
        "Vončinina", "Vrazovo šetalište", "Wickerhauserova", "Zamenhofova",
        "Zamenhofove", "Zavojna", "Zelengaj", "Zeleni dol",
        "Zelenjak", "Zmajevac", "Zvonarnička",
    )

    states = (
        "Zagrebačka",
        "Krapinsko-zagorska",
        "Sisačko-moslavačka",
        "Karlovačka",
        "Varaždinska",
        "Koprivničko-križevačka",
        "Bjelovarsko-bilogorska",
        "Primorsko-goranska",
        "Ličko-senjska",
        "Virovitičko-podravska",
        "Požeško-slavonska",
        "Brodsko-posavska",
        "Zadarska",
        "Osječko-baranjska",
        "Šibensko-kninska",
        "Vukovarsko-srijemska",
        "Splitsko-dalmatinska",
        "Istarska",
        "Dubrovačko-neretvanska",
        "Međimurska",
        "Grad Zagreb",
    )

    countries = (
        "Afganistan", "Alandski otoci", "Albanija", "Alžir", "Američka Samoa",
        "Američki Djevičanski Otoci", "Andora", "Angola", "Anguila",
        "Antarktik", "Antigua i Barbuda", "Argentina", "Armenija", "Aruba",
        "Australija", "Austrija", "Azerbajdžan", "Bahami",
        "Bahrein", "Bangladeš", "Barbados", "Belgija", "Belize",
        "Benin", "Bermuda", "Bjelorusija", "Bocvana", "Bolivija",
        "Bosna i Hercegovina", "Božićni Otok", "Brazil",
        "Britanski Djevičanski Otoci", "Britanski Teritorij Indijskog Oceana",
        "Brunei Darussalam", "Bugarska", "Burkina Faso", "Burundi", "Butan",
        "Cipar", "Crna Gora", "Curacao", "Čad", "Čile", "Danska", "Dominika",
        "Dominikanska Republika", "Džibuti", "Egipat", "Ekvador",
        "Ekvatorska Gvineja", "El Salvador", "Eritreja", "Estonija",
        "Etiopija", "Falklandi", "Farski Otoci", "Fidži", "Filipini", "Finska",
        "Francuska", "Francuska Gvajana", "Francuska Polinezija",
        "Francuski Južni Teritoriji", "Gabon", "Gambija", "Gana", "Gibraltar",
        "Vatikan", "Grčka", "Grenada", "Grenland", "Gruzija", "Guadeloupe",
        "Guam", "Guernsey", "Gvajana", "Gvatemala", "Gvineja", "Gvineja Bisau",
        "Haiti", "Honduras", "Hong Kong", "Hrvatska", "Indija", "Indonezija",
        "Irak", "Iran, Islamska Republika", "Irska", "Island", "Isle Of Man",
        "Istočni Timor", "Italija", "Izrael", "Jamajka", "Japan", "Jemen",
        "Jersey", "Jordan", "Južna Afrika",
        "Južna Gruzija i Južni Sendvič Otoci", "Kajmanski Otoci", "Kambodža",
        "Kamerun", "Kanada", "Katar", "Kazakstan", "Kenija", "Kina",
        "Kirgistan", "Kiribati", "Kokosovi Otoci", "Kolumbija", "Komori",
        "Kongo", "Kongo, Demokratska Republika", "Koreja, Južna",
        "Koreja, Sjeverna", "Kosovo", "Kostarika", "Kuba", "Kukovi Otoci",
        "Kuvajt", "Laoska Narodna Demokratska Republika", "Latvija", "Lesoto",
        "Libanon", "Liberija", "Libijska Arapska Džamahirija", "Lihtenštajn",
        "Litva", "Luksemburg", "Madagaskar", "Mađarska", "Majote", "Makao",
        "Makedonija", "Malavi", "Maldivi Maldives", "Malezija", "Mali",
        "Malta", "Maroko", "Maršalovi Otoci", "Martinik", "Mauricijus",
        "Mauritanija", "Meksiko", "Mijanmar", "Mikronezija",
        "Moldavija, Republika", "Monako", "Mongolija", "Montserat", "Mozambik",
        "Namibija", "Nauru", "Nepal", "Niger", "Nigerija", "Nikaragva", "Niue",
        "Nizozemska", "Norveška", "Nova Kaledonija", "Novi Zeland", "Njemačka",
        "Obala Slonovače", "Oman", "Otok Bouvet",
        "Otok Heard i Otoci McDonald", "Otok Norfolk", "Pakistan", "Palau",
        "Palestinsko Područje", "Panama", "Papua Nova Gvineja", "Paragvaj",
        "Peru", "Pitcairn", "Poljska Poland", "Portoriko", "Portugal",
        "Republika Češka", "Reunion", "Ruanda", "Rumunjska", "Rusija",
        "Salamunovi Otoci", "Samoa", "San Marino", "São Tomé ai Príncipe",
        "Saudijska Arabija", "Sejšeli", "Senegal", "Sijera Leone", "Singapur",
        "Sint Maarten", "Sirija", "Sjedinjene Američke Države",
        "Sjeverni Marijanski Otoci", "Slovačka", "Slovenija", "Somalija",
        "Južni Sudan", "Srbija", "Srednjoafrička Republika", "Sudan",
        "Surinam", "Svalbard i Jan Mayen", "Svaziland", "Sveta Helena",
        "Sveti Bartolomej", "Sveti Martin", "Sveti Petar i Miguel",
        "Sv. Kristofor i Nevis", "Sv. Lucija", "Sv. Vincent i Grenadini",
        "Španjolska", "Šri Lanka", "Švedska", "Švicarska", "Tadžikistan",
        "Tajland", "Tajvan", "Tanzanija", "Togo", "Tokelau", "Tonga",
        "Trinidad i Tobago", "Tunis", "Turkmenistan", "Turkski i Kaikos Otoci",
        "Turska", "Tuvalu", "Uganda",
        "Ujedinjene Države Manjih Pacifičkih Otoka",
        "Ujedinjeni Arapski Emirati", "Ukrajina", "Urugvaj", "Uzbekistan",
        "Vanuatu", "Velika Britanija", "Venezuela", "Vijetnam",
        "Wallis i Futuna", "Zambija", "Zapadna Sahara", "Zeleni Rt",
    )

    def city_name(self):
        return self.random_element(self.cities)

    def street_name(self):
        return self.random_element(self.streets)

    def state(self):
        return self.random_element(self.states)
