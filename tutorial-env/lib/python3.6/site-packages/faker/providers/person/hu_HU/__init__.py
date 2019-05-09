# coding=utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from .. import Provider as PersonProvider


# Data source
#
# Data for this provider comes from the following source:
# Ministry of Interior, Deputy Secretary of State for Records
#
# 100 most frequent family names on record, 2016:
# http://www.kekkh.gov.hu/letoltes/statisztikak/kozerdeku_csaladnev_2016.xls
#
# 100 most frequent first names on record, 2016:
# http://www.kekkh.gov.hu/letoltes/statisztikak/kozerdeku_utonevek_2016.xls
#
# This information is in the public domain by virtue of being an official
# report issued by a part of the Government of Hungary.

# TODO:
# There is no accurate information about the frequency of differzent name
# schemata, so for that reason, equal frequency will be assumed in most cases,
# except for combinations that are widely known as headed for obsolescence.
# If such information could be obtained, the relative frequencies could be
# adjusted to yield a more realistic distribution of name patterns/schemata.


class Provider(PersonProvider):
    formats_male = OrderedDict((
        ('{{last_name}} {{first_name_male}}', 0.1),
        ('{{last_name}} {{last_name}} {{first_name_male}}', 0.1),
        ('{{last_name}} {{first_name_male}} {{first_name_male}}', 0.1),
        ('{{first_name_male_abbreviated}} {{last_name}} {{first_name_male}}', 0.1),
        ('{{last_name}} {{first_name_male_abbreviated}} {{first_name_male}}', 0.1),
        ('{{prefix}} {{last_name}} {{first_name_male}}', 0.05),
        ('{{prefix}} {{last_name}} {{last_name}} {{first_name_male}}', 0.05),
        ('{{prefix}} {{last_name}} {{first_name_male}} {{first_name_male}}', 0.05),
        ('{{prefix}} {{first_name_male_abbreviated}} {{last_name}} {{first_name_male}}', 0.05),
        ('{{prefix}} {{last_name}} {{first_name_male_abbreviated}} {{first_name_male}}', 0.05)))

    formats_female = OrderedDict((
        ('{{last_name}} {{first_name_female}}', 0.1),
        ('{{last_name}} {{last_name}} {{first_name_female}}', 0.1),
        ('{{last_name}} {{first_name_female}} {{first_name_female}}', 0.1),
        ('{{first_name_female_abbreviated}} {{last_name}} {{first_name_female}}', 0.1),
        ('{{last_name}} {{first_name_female_abbreviated}} {{first_name_female}}', 0.1),
        ('{{prefix}} {{last_name}} {{first_name_female}}', 0.05),
        ('{{prefix}} {{last_name}} {{last_name}} {{first_name_female}}', 0.05),
        ('{{prefix}} {{last_name}} {{first_name_female}} {{first_name_female}}', 0.05),
        ('{{prefix}} {{first_name_female_abbreviated}} {{last_name}} {{first_name_female}}', 0.05),
        ('{{prefix}} {{last_name}} {{first_name_female_abbreviated}} {{first_name_female}}', 0.05),
        ('{{last_name}}né {{last_name}} {{first_name_female}}', 0.1),
        ('{{last_name}}né {{last_name}} {{first_name_female}} {{first_name_female}}', 0.1),
        ('{{last_name}}né {{last_name}} {{first_name_female}} {{first_name_female}}', 0.05),
        ('{{last_name}} {{first_name_male}}né', 0.05),
        ('{{last_name}} {{first_name_male}}né {{last_name}} {{first_name_female}}', 0.1),
        ('{{prefix}} {{last_name}}né {{last_name}} {{first_name_female}}', 0.1),
        ('{{prefix}} {{last_name}}né {{last_name}} {{first_name_female}} {{first_name_female}}', 0.05),
        ('{{prefix}} {{last_name}}né {{last_name}} {{first_name_female}} {{first_name_female}}', 0.05),
        ('{{prefix}} {{last_name}} {{first_name_male}}né', 0.1),
        ('{{prefix}} {{last_name}} {{first_name_male}}né {{last_name}} {{first_name_female}}', 0.05),
        ('{{last_name}}né {{prefix}} {{last_name}} {{first_name_female}}', 0.1),
        ('{{last_name}}né {{prefix}} {{last_name}} {{first_name_female}} {{first_name_female}}', 0.05),
    ))

    formats = formats_male.copy()
    formats.update(formats_female)

    last_names = OrderedDict((
        ("Nagy", 0.06992), ("Kovács", 0.06457), ("Tóth", 0.06316),
        ("Szabó", 0.06234), ("Horváth", 0.05995), ("Varga", 0.041),
        ("Kiss", 0.03891), ("Molnár", 0.03189), ("Németh", 0.02715),
        ("Farkas", 0.02499), ("Balogh", 0.02468), ("Papp", 0.01567),
        ("Takács", 0.01535), ("Juhász", 0.01516), ("Lakatos", 0.01486),
        ("Mészáros", 0.01183), ("Oláh", 0.01161), ("Simon", 0.01129),
        ("Rácz", 0.01063), ("Fekete", 0.01021), ("Szilágyi", 0.00959),
        ("Török", 0.0079), ("Fehér", 0.00786), ("Balázs", 0.00771),
        ("Gál", 0.00756), ("Kis", 0.00730), ("Szűcs", 0.00709),
        ("Kocsis", 0.00700), ("Orsós", 0.00692), ("Pintér", 0.006),
        ("Fodor", 0.00686), ("Szalai", 0.00628), ("Sipos", 0.00620),
        ("Magyar", 0.0061), ("Lukács", 0.00611), ("Gulyás", 0.00591),
        ("Biró", 0.00576), ("Király", 0.00560), ("László", 0.00548),
        ("Katona", 0.00548), ("Jakab", 0.00541), ("Bogdán", 0.00536),
        ("Balog", 0.0053), ("Sándor", 0.0052), ("Boros", 0.00515),
        ("Fazekas", 0.005), ("Kelemen", 0.00500), ("Váradi", 0.00500),
        ("Antal", 0.00490), ("Somogyi", 0.00487), ("Orosz", 0.00484),
        ("Fülöp", 0.00480), ("Veres", 0.00470), ("Vincze", 0.00468),
        ("Hegedűs", 0.00458), ("Budai", 0.00453), ("Deák", 0.00449),
        ("Pap", 0.00442), ("Bálint", 0.00435), ("Pál", 0.00427),
        ("Illés", 0.0042), ("Vass", 0.00420), ("Szőke", 0.00419),
        ("Vörös", 0.00418), ("Bognár", 0.00416), ("Fábián", 0.00415),
        ("Lengyel", 0.00414), ("Bodnár", 0.00409), ("Szücs", 0.00403),
        ("Hajdu", 0.00391), ("Halász", 0.00390), ("Jónás", 0.00388),
        ("Máté", 0.00371), ("Székely", 0.00367), ("Kozma", 0.00366),
        ("Gáspár", 0.00364), ("Pásztor", 0.00356), ("Bakos", 0.00354),
        ("Dudás", 0.00348), ("Major", 0.00347), ("Orbán", 0.00343),
        ("Hegedüs", 0.00342), ("Virág", 0.00341), ("Barna", 0.00335),
        ("Novák", 0.00334), ("Soós", 0.00331), ("Tamás", 0.00326),
        ("Nemes", 0.00326), ("Pataki", 0.0032), ("Balla", 0.00313),
        ("Faragó", 0.00312), ("Kerekes", 0.0031), ("Borbély", 0.00311),
        ("Barta", 0.00308), ("Péter", 0.0030), ("Szekeres", 0.00306),
        ("Csonka", 0.00305), ("Mezei", 0.00302), ("Márton", 0.00300),
        ("Sárközi", 0.00298),
    ))

    first_names_male = OrderedDict((
        ("László", 0.06640477), ("István", 0.060906051), ("József",
                                                          0.054476881), ("János", 0.047506017),
        ("Zoltán", 0.045579697), ("Sándor", 0.037170944), ("Gábor",
                                                           0.035546303), ("Ferenc", 0.034065759),
        ("Attila", 0.032146512), ("Péter", 0.03083703), ("Tamás",
                                                         0.030257321), ("Zsolt", 0.025204158),
        ("Tibor", 0.023296182), ("András", 0.021678391), ("Csaba",
                                                          0.020367141), ("Imre", 0.019339667),
        ("Lajos", 0.017901558), ("György", 0.01695188), ("Balázs",
                                                         0.015569685), ("Gyula", 0.014295123),
        ("Mihály", 0.013628337), ("Róbert", 0.013385668), ("Károly",
                                                           0.013181456), ("Dávid", 0.01315184),
        ("Dániel", 0.012373665), ("Ádám", 0.012290124), ("Béla",
                                                         0.012279294), ("Krisztián", 0.011589081),
        ("Miklós", 0.010985283), ("Norbert", 0.010746593), ("Bence",
                                                            0.010403586), ("Máté", 0.009479986),
        ("Pál", 0.007890264), ("Gergő", 0.007554993), ("Roland",
                                                       0.007535765), ("Szabolcs", 0.007522062),
        ("Bálint", 0.007021254), ("Levente", 0.006948763), ("Márk",
                                                            0.006873178), ("Richárd", 0.006811074),
        ("Antal", 0.006583213), ("Gergely", 0.006408174), ("Ákos",
                                                           0.006278662), ("Viktor", 0.005872447),
        ("Árpád", 0.005217153), ("Márton", 0.005061783), ("Géza",
                                                          0.005036367), ("Kristóf", 0.004518984),
        ("Milán", 0.003956735), ("Dominik", 0.003924247), ("Patrik",
                                                           0.003911428), ("Martin", 0.003747439),
        ("Barnabás", 0.003645333), ("Jenő", 0.003619917), ("Kálmán",
                                                           0.003613728), ("Marcell", 0.003571515),
        ("Áron", 0.003219668), ("Mátyás", 0.003028495), ("Ernő",
                                                         0.002998879), ("Endre", 0.002830912),
        ("Botond", 0.00282605), ("Zsombor", 0.002768366), ("Dezső",
                                                           0.002557523), ("Olivér", 0.002524814),
        ("Nándor", 0.002520394), ("Szilárd",
                                  0.002422044), ("Erik", 0.002421381), ("Alex", 0.0023248),
        ("Benedek", 0.002119924), ("Vilmos", 0.002113515), ("Kornél",
                                                            0.002018481), ("Zalán", 0.001970964),
        ("Dénes", 0.001921458), ("Ottó", 0.001901788), ("Benjámin",
                                                        0.001738241), ("Bertalan", 0.001700227),
        ("Kevin", 0.001668623), ("Adrián", 0.001550603), ("Rudolf",
                                                          0.001386172), ("Noel", 0.001381973),
        ("Albert", 0.001355673), ("Vince", 0.001353463), ("Ervin",
                                                          0.001182622), ("Győző", 0.001125823),
        ("Zsigmond", 0.001120519), ("Andor", 0.001057531), ("Iván",
                                                            0.001016202), ("Szilveszter", 0.001010014),
        ("Gusztáv", 0.000994985), ("Barna", 0.000986808), ("Ábel",
                                                           0.000969569), ("Hunor", 0.000940396),
        ("Arnold", 0.000931777), ("Csongor", 0.00092824), ("Elemér",
                                                           0.000894868), ("Krisztofer", 0.000891111),
        ("Bendegúz", 0.000868347), ("Emil", 0.000791656), ("Tivadar", 0.000786573), ("Henrik", 0.000758063)))

    first_names_female = OrderedDict((
        ("Mária", 0.076200074), ("Erzsébet",
                                 0.058002384), ("Katalin", 0.0429636), ("Éva", 0.039004017),
        ("Ilona", 0.038027669), ("Anna", 0.030819538), ("Zsuzsanna",
                                                        0.029737292), ("Margit", 0.024148354),
        ("Judit", 0.020956031), ("Ágnes", 0.020891678), ("Andrea",
                                                         0.020768845), ("Ildikó", 0.019861817),
        ("Julianna", 0.019458091), ("Erika", 0.018991368), ("Krisztina",
                                                            0.017491847), ("Irén", 0.015454477),
        ("Eszter", 0.014382165), ("Mónika", 0.014128821), ("Magdolna",
                                                           0.013536554), ("Edit", 0.013129441),
        ("Gabriella", 0.012887838), ("Szilvia", 0.012663621), ("Anita",
                                                               0.011554053), ("Viktória", 0.011388318),
        ("Anikó", 0.011180584), ("Márta", 0.010886596), ("Tímea",
                                                         0.010327747), ("Rozália", 0.009782898),
        ("Piroska", 0.009699353), ("Ibolya", 0.00922134), ("Klára",
                                                           0.008981769), ("Tünde", 0.008838839),
        ("Dóra", 0.008803841), ("Zsófia", 0.008600397), ("Alexandra",
                                                         0.007886652), ("Veronika", 0.00777443),
        ("Gizella", 0.007579567), ("Csilla", 0.007395768), ("Nikolett",
                                                            0.006972849), ("Melinda", 0.006857693),
        ("Réka", 0.0068385), ("Nóra", 0.006794469), ("Terézia",
                                                     0.006777535), ("Adrienn", 0.006753826),
        ("Beáta", 0.006526674), ("Marianna", 0.006462547), ("Vivien",
                                                            0.006299747), ("Renáta", 0.00626091),
        ("Barbara", 0.006076434), ("Enikő", 0.006052499), ("Bernadett",
                                                           0.005964438), ("Rita", 0.005917472),
        ("Brigitta", 0.005875926), ("Edina", 0.005745866), ("Hajnalka",
                                                            0.005696191), ("Gyöngyi", 0.005616484),
        ("Petra", 0.005609033), ("Boglárka", 0.005329496), ("Orsolya",
                                                            0.005328141), ("Jolán", 0.005184534),
        ("Noémi", 0.005078861), ("Etelka", 0.004833419), ("Valéria",
                                                          0.00472594), ("Fanni", 0.004716682),
        ("Borbála", 0.004701553), ("Annamária",
                                   0.004528367), ("Kitti", 0.00439334), ("Teréz", 0.004384985),
        ("Nikoletta", 0.004310021), ("Laura", 0.004266893), ("Emese",
                                                             0.004212702), ("Lilla", 0.004193961),
        ("Hanna", 0.003921198), ("Aranka", 0.003884844), ("Kinga",
                                                          0.003755914), ("Klaudia", 0.003710077),
        ("Anett", 0.003661305), ("Róza", 0.003621339), ("Lili",
                                                        0.003436636), ("Zita", 0.00343212),
        ("Dorina", 0.003412476), ("Emma", 0.003374994), ("Beatrix",
                                                         0.003364381), ("Zsanett", 0.003276772),
        ("Sára", 0.003156873), ("Bianka", 0.003061135), ("Rózsa",
                                                         0.003006041), ("Jázmin", 0.002952527),
        ("Luca", 0.002949817), ("Júlia", 0.002917754), ("Diána",
                                                        0.002841434), ("Henrietta", 0.002798759),
        ("Györgyi", 0.002731471), ("Irma", 0.00272131), ("Dorottya",
                                                         0.002585154), ("Bettina", 0.002574316),
        ("Mariann", 0.002569349), ("Virág", 0.002557156), ("Gréta", 0.002515835), ("Rebeka", 0.002513351)))

    first_names = first_names_male.copy()
    first_names.update(first_names_female)

    prefixes = OrderedDict((('Dr.', 0.95), ('Prof. Dr.', 0.05)))

    def first_name_male_abbreviated(self):
        if hasattr(self, 'first_names_male'):
            return self.random_element(self.first_names_male)[0] + "."
        return self.first_name()[0]

    def first_name_female_abbreviated(self):
        if hasattr(self, 'first_names_female'):
            return self.random_element(self.first_names_female)[0] + "."
        return self.first_name()[0]
