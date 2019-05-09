# coding=utf-8

from __future__ import unicode_literals
from collections import OrderedDict

from .. import Provider as AddressProvider


class Provider(AddressProvider):
    street_suffixes = OrderedDict(
        (('utca', 0.75), ('út', 0.1), ('tér', 0.1), ('köz', 0.001), ('körút', 0.001), ('sétány', 0.001)))

    street_name_formats = (
        '{{frequent_street_name}} {{street_suffix}}',
        '{{real_city_name}}i {{street_suffix}}',
        '{{city_part}}{{city_suffix}}i {{street_suffix}}',
        '{{city_prefix}}{{city_part}}i {{street_suffix}}')

    #   Currently deprecated.
    #   secondary_address_formats = ("#.em #.", "##. em. #.")

    city_formats = ('{{city_prefix}}{{city_part}}{{city_suffix}}',
                    '{{city_part}}{{city_suffix}}', '{{real_city_name}}')

    street_address_formats = ('{{street_name}} {{building_number}}',)

    address_formats = ("{{street_address}}\n{{postcode}} {{city}}",)

    frequent_street_names = (
        'Ady Endre',
        'Dózsa György',
        'Petőfi',
        'Petőfi Sándor',
        'Arany János',
        'Béke',
        'Szabadság',
        'Kossuth',
        'József Attila')

    # The 'real city name' generator includes a number of real cities of
    # Hungary that no generator could feasibly dispense. Please note that the
    # post code generator is, at this point, not capable of generating a
    # fitting post code. In Hungary, post codes are determined by the county of
    # the place (see the county generator), and for this reason, often there
    # will be a discrepancy. A patch is in the works - until then, use
    # Wikipedia to resolve postcode issues.
    #
    # This generator was created by collecting the 30 largest Hungarian places
    # by population, based on the Hungarian Gazetteer generated with effect as
    # of 01 January 2016 (http://www.ksh.hu/docs/hun/hnk/hnk_2016.pdf).

    real_city_names = (
        'Budapest',
        'Debrecen',
        'Szeged',
        'Miskolc',
        'Pécs',
        'Győr',
        'Nyíregyháza',
        'Kecskemét',
        'Székesfehérvár',
        'Szombathely',
        'Szolnok',
        'Tatabánya',
        'Érd',
        'Kaposvár',
        'Sopron',
        'Veszprém',
        'Békéscsaba',
        'Zalaegerszeg',
        'Eger',
        'Nagykanizsa',
        'Dunaújváros',
        'Hódmezővásárhely',
        'Dunakeszi',
        'Szigetszentmiklós',
        'Cegléd',
        'Baja',
        'Salgótarján',
        'Ózd',
        'Vác',
        'Mosonmagyaróvár')

    city_prefs = (
        'kis',
        'nagy',
        'szent',
        'duna',
        'tisza',
        'alsó',
        'felső',
        'belső',
        'bakony',
        'vác',
        'mező',
        'nyék',
        'nyír',
        'balaton',
        'borsod',
        'buda',
        'hajdú',
        'kun',
        'moson',
        'pilis',
        'új',
        'egyházas',
        'dráva',
        'magyar',
        'mátra',
        'somogy',
        'lajos',
        'bács',
        'békés',
        'puszta',
        'orosz',
        'rác',
        'szerb',
        'német',
        'török')

    city_parts = (
        'híd',
        'györgy',
        'mindszent',
        'kereszt',
        'márton',
        'hát',
        'hetven',
        'mellék',
        'tamási',
        'tapolca',
        'fürdő',
        'liget',
        'szék',
        'tót',
        '')

    city_suffixes = (
        'háza',
        'németi',
        'devecser',
        'fa',
        'nádasd',
        'apáti',
        'falu',
        'falva',
        'vég',
        'vár',
        'vára',
        'várad',
        'hida',
        'kövesd',
        'bánya',
        'halas',
        'berény',
        'kőrös',
        'haraszti',
        'város')

    counties = (
        'Bács-Kiskun',
        'Baranya',
        'Békés',
        'Borsod-Abaúj-Zemplén',
        'Csongrád',
        'Fejér',
        'Győr-Moson-Sopron',
        'Hajdú-Bihar',
        'Heves',
        'Jász-Nagykun-Szolnok',
        'Komárom-Esztergom',
        'Nógrád',
        'Pest',
        'Somogy',
        'Szabolcs-Szatmár-Bereg',
        'Tolna',
        'Vas',
        'Veszprém',
        'Zala')

    countries = (
        "Afganisztán", "Aland-szigetek", "Albánia", "Algéria", "Amerikai Szamoa", "Amerikai Virgin-szigetek", "Andorra",
        "Angola", "Anguilla", "Antarktisz", "Antigua és Barbuda", "Apostoli Szentszék", "Argentína", "Aruba",
        "Ausztrália", "Ausztria", "Amerikai Egyesült Államok Külső Szigetei", "Azerbajdzsán", "Bahama-szigetek",
        "Bahrein", "Banglades", "Barbados", "Fehéroroszország", "Belgium", "Belize", "Benin", "Bermuda", "Bhután",
        "Bissa -Guinea", "Bolívia", "Bosznia-Hercegovina", "Botswana", "Bouvet-sziget", "Brazília",
        "Brit Indiai-óceáni Terület", "Brit Virgin - szigetek", "Brunei", "Bulgária", "Burkina Faso", "Burundi",
        "Chile", "Ciprus", "Comore-szigetek", "Cook-szigetek", "Costa Rica", "Csád", "Csehország", "Dánia",
        "Dél-Afrika", "Dél-Korea", "Dominika", "Dominikai Köztársaság", "Dzsibuti", "Ecuador", "Egyenlítői-Guinea",
        "Egyesült Államok", "Egyesült Arab Emírségek", "Egyesült Királyság", "Egyiptom", "Elefántcsontpart", "Eritrea",
        "Északi Mariana-szigetek", "Észak-Korea", "Észtország", "Etiópia", "Falkland-szigetek", "Feröer szigetek",
        "Fidzsi-szigetek", "Finnország", "Francia Déli Területek", "Francia Guyana", "Francia Polinézia",
        "Franciaország", "Fülöp-szigetek", "Gabon", "Gambia", "Ghána", "Gibraltár", "Görögország", "Grenada",
        "Grönland", "Grúzia", "Guadeloupe", "Guam", "Guatemala", "Guinea", "Guyana", "Haiti", "Holland Antillák",
        "Hollandia", "Honduras", "Hongkong", "Horvátország", "India", "Indonézia", "Irak", "Irán", "Írország", "Izland",
        "Izrael", "Jamaica", "Japán", "Jemen", "Jordánia", "Kajmán-szigetek", "Kambodzsa", "Kamerun", "Kanada",
        "Karácsony-sziget", "Katar", "Kazahsztán", "Kelet-Timor", "Kenya", "Kína", "Kirgizisztán", "Kiribati",
        "Keeling-szigetek", "Kolumbia", "Kongó", "Kongói Demokratikus Köztársaság", "Közép-afrikai Köztársaság", "Kuba",
        "Kuvait", "Laosz", "Lengyelország", "Lesotho", "Lettország", "Libanon", "Libéria", "Líbia", "Liechtenstein",
        "Litvánia", "Luxemburg", "Macedónia", "Madagaszkár", "Magyarország", "Makaó", "Malajzia", "Malawi",
        "Maldív-szigetek", "Mali", "Málta", "Marokkó", "Marshall-szigetek", "Martinique", "Mauritánia", "Mauritius",
        "Mayotte", "Mexikó", "Mianmar", "Mikronézia", "Moldova", "Monaco", "Mongólia", "Montenegró", "Montserrat",
        "Mozambik", "Namíbia", "Nauru", "Németország", "Nepál", "Nicaragua", "Niger", "Nigéria", "Niue",
        "Norfolk-sziget", "Norvégia", "Nyugat-Szahara", "Olaszország", "Omán", "Oroszország", "Örményország",
        "Pakisztán", "Palau", "Panama", "Pápua", "Új-Guinea", "Paraguay", "Peru", "Pitcairn-szigetek", "Portugália",
        "Puerto Rico", "Réunion", "Románia", "Ruanda", "Saint Kitts és Nevis", "Saint Lucia",
        "Saint-Pierre és Miquelon", "Saint Vincent és Grenadine-szigetek", "Salamon-szigetek", "Salvador", "San Marino",
        "São Tomé és Príncipe", "Seychelle-szigetek", "Sierra Leone", "Spanyolország", "Srí Lanka", "Suriname", "Svájc",
        "Svalbard szigetek", "Svédország", "Szamoa", "Szaúdi-Arábia", "Szenegál", "Szent Ilona", "Szerbia", "Szingapúr",
        "Szíria", "Szlovákia", "Szlovénia", "Szomália", "Szudán", "Szváziföld", "Tádzsikisztán", "Tajvan", "Tanzánia",
        "Thaiföld", "Togo", "Tokelau-szigetek", "Tonga", "Törökország", "Trinidad és Tobago", "Tunézia",
        "Turks- és Caicos-szigetek", "Tuvalu", "Türkmenisztán", "Uganda", "Új-Kaledónia", "Új-Zéland", "Ukrajna",
        "Uruguay", "Üzbegisztán", "Vanuatu", "Venezuela", "Vietnam", "Wallis és Futuna", "Zambia", "Zimbabwe",
        "Zöld-foki szigetek")

    def county(self):
        return self.random_element(self.counties)

    def street_address_with_county(self):
        return "{street_address}\n{county} megye\n{postcode} {city}".format(
            street_address=self.street_address(),
            county=self.county(),
            postcode=self.postcode(),
            city=self.city().capitalize())

    def city_prefix(self):
        return self.random_element(self.city_prefs)

    def city_part(self):
        return self.random_element(self.city_parts)

    def real_city_name(self):
        return self.random_element(self.real_city_names)

    def frequent_street_name(self):
        return self.random_element(self.frequent_street_names)

    def postcode(self):
        return "H-{}{}{}{}".format(
            super(
                Provider, self).random_digit_not_null(), super(
                Provider, self).random_digit(), super(
                Provider, self).random_digit(), super(
                    Provider, self).random_digit())

    def street_name(self):
        return super(Provider, self).street_name().capitalize()

    def building_number(self):
        numeric_part = super(Provider, self).random_int(1, 250)
        return str(numeric_part) + "."
