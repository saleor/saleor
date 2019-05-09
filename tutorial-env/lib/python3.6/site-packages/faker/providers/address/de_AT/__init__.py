# coding=utf-8

from __future__ import unicode_literals
from ..de import Provider as AddressProvider


class Provider(AddressProvider):

    city_formats = ('{{city_name}}', )

    city_with_postcode_formats = ('{{postcode}} {{city}}', )

    street_name_formats = (
        '{{first_name}}-{{last_name}}-{{street_suffix_long}}',
        '{{last_name}}{{street_suffix_short}}',
    )
    street_address_formats = ('{{street_name}} {{building_number}}', )
    address_formats = ('{{street_address}}\n{{postcode}} {{city}}', )

    building_number_formats = ('###', '##', '#', '#/#')

    street_suffixes_long = (
        'Gasse', 'Platz', 'Ring', 'Straße', 'Weg',
    )
    street_suffixes_short = (
        'gasse', 'platz', 'ring', 'straße', 'str.', 'weg',
    )

    # https://en.wikipedia.org/wiki/List_of_postal_codes_in_Austria
    postcode_formats = (
        '1###', '2###', '3###', '4###', '5###', '6###', '7###', '8###', '9###',
    )

    # https://en.wikipedia.org/wiki/List_of_cities_and_towns_in_Austria
    cities = (
        'Allentsteig', 'Altheim', 'Althofen', 'Amstetten', 'Ansfelden', 'Attnang-Puchheim',
        'Bad Aussee', 'Bad Hall', 'Bad Ischl', 'Bad Leonfelden', 'Bad Radkersburg',
        'Bad Sankt Leonhard im Lavanttal', 'Bad Vöslau', 'Baden', 'Bärnbach', 'Berndorf',
        'Bischofshofen', 'Bleiburg', 'Bludenz', 'Braunau am Inn', 'Bregenz',
        'Bruck an der Leitha', 'Bruck an der Mur', 'Deutsch-Wagram', 'Deutschlandsberg',
        'Dornbirn', 'Drosendorf-Zissersdorf 1', 'Dürnstein', 'Ebenfurth', 'Ebreichsdorf',
        'Eferding', 'Eggenburg', 'Eisenerz', 'Eisenstadt', 'Enns', 'Fehring', 'Feldbach',
        'Feldkirch', 'Feldkirchen', 'Ferlach', 'Fischamend', 'Frauenkirchen', 'Freistadt',
        'Friedberg', 'Friesach', 'Frohnleiten', 'Fürstenfeld', 'Gallneukirchen', 'Gänserndorf',
        'Geras', 'Gerasdorf bei Wien', 'Gföhl', 'Gleisdorf', 'Gloggnitz', 'Gmünd',
        'Gmünd in Kärnten', 'Gmunden', 'Graz', 'Grein', 'Grieskirchen', 'Groß-Enzersdorf',
        'Groß-Gerungs', 'Groß-Siegharts', 'Güssing', 'Haag', 'Hainburg an der Donau', 'Hainfeld',
        'Hall in Tirol', 'Hallein', 'Hardegg', 'Hartberg', 'Heidenreichstein', 'Herzogenburg',
        'Imst', 'Innsbruck', 'Jennersdorf', 'Judenburg', 'Kapfenberg', 'Kindberg', 'Klagenfurt',
        'Klosterneuburg', 'Knittelfeld', 'Köflach', 'Korneuburg', 'Krems an der Donau', 'Kufstein',
        'Laa an der Thaya', 'Laakirchen', 'Landeck', 'Langenlois', 'Leibnitz', 'Leoben', 'Lienz',
        'Liezen', 'Lilienfeld', 'Linz', 'Litschau', 'Maissau', 'Mank', 'Mannersdorf am Leithagebirge',
        'Marchegg', 'Marchtrenk', 'Mariazell', 'Mattersburg', 'Mattighofen', 'Mautern an der Donau',
        'Melk', 'Mistelbach an der Zaya', 'Mödling', 'Murau', 'Mureck', 'Mürzzuschlag', 'Neulengbach',
        'Neumarkt am Wallersee', 'Neunkirchen', 'Neusiedl am See', 'Oberndorf bei Salzburg',
        'Oberpullendorf', 'Oberwart', 'Oberwälz', 'Perg', 'Peuerbach', 'Pinkafeld', 'Pöchlarn',
        'Poysdorf', 'Pregarten', 'Pulkau', 'Purbach am Neusiedler See', 'Purkersdorf',
        'Raabs an der Thaya', 'Radenthein', 'Radstadt', 'Rattenberg', 'Retz', 'Ried im Innkreis',
        'Rohrbach in Oberösterreich', 'Rottenmann', 'Rust', 'Saalfelden am Steinernen Meer',
        'Salzburg', 'Sankt Andrä im Lavanttal', 'Sankt Johann im Pongau', 'Sankt Pölten',
        'Sankt Valentin', 'Sankt Veit an der Glan', 'Schärding', 'Scheibbs', 'Schladming',
        'Schrattenthal', 'Schrems', 'Schwanenstadt', 'Schwaz', 'Schwechat', 'Spittal an der Drau',
        'Stadtschlaining', 'Steyr', 'Steyregg', 'Stockerau', 'Straßburg', 'Ternitz', 'Traiskirchen',
        'Traismauer', 'Traun', 'Trieben', 'Trofaiach', 'Tulln an der Donau', 'Villach', 'Vils',
        'Vöcklabruck', 'Voitsberg', 'Völkermarkt', 'Waidhofen an der Thaya', 'Waidhofen an der Ybbs',
        'Weitra', 'Weiz', 'Wels', 'Wien', 'Wiener Neustadt', 'Wieselburg', 'Wilhelmsburg', 'Wolfsberg',
        'Wolkersdorf', 'Wörgl', 'Ybbs an der Donau', 'Zell am See', 'Zeltweg', 'Zistersdorf', 'Zwettl',
    )

    # https://en.wikipedia.org/wiki/States_of_Austria
    states = (
        'Wien', 'Steiermark', 'Burgenland', 'Tirol', 'Niederösterreich',
        'Oberösterreich', 'Salzburg', 'Kärnten', 'Vorarlberg',
    )

    def street_suffix_short(self):
        return self.random_element(self.street_suffixes_short)

    def street_suffix_long(self):
        return self.random_element(self.street_suffixes_long)

    def city_name(self):
        return self.random_element(self.cities)

    def state(self):
        return self.random_element(self.states)

    def city_with_postcode(self):
        pattern = self.random_element(self.city_with_postcode_formats)
        return self.generator.parse(pattern)
