# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as PersonProvider


class Provider(PersonProvider):
    # https://en.wikipedia.org/wiki/Demographics_of_Estonia#Ethnic_groups
    # Main population groups in Estonia are Estonians and ethnic Russians:
    # About 70% of the population are Estonians and about 25% are Russians
    est_rat = 0.7
    rus_rat = 1.0 - est_rat
    formats = {'{{first_name_est}} {{last_name_est}}': est_rat,
               '{{first_name_rus}} {{last_name_rus}}': rus_rat}

    formats_male = {'{{first_name_male_est}} {{last_name_est}}': est_rat,
                    '{{first_name_male_rus}} {{last_name_rus}}': rus_rat}
    formats_female = {'{{first_name_female_est}} {{last_name_est}}': est_rat,
                      '{{first_name_female_rus}} {{last_name_rus}}': rus_rat}

    prefixes_neutral = ('doktor', 'dr', 'prof')
    prefixes_male = ('härra', 'hr') + prefixes_neutral
    prefixes_female = ('proua', 'pr') + prefixes_neutral
    prefixes = set(prefixes_male + prefixes_female)

    suffixes = ('PhD', 'MSc', 'BSc')

    # source: http://www.stat.ee/public/apps/nimed/TOP
    # TOP 50 male names in 2017 according to the Statistics Estonia
    first_names_male_est = ('Aivar', 'Aleksander', 'Alexander', 'Andres',
                            'Andrus', 'Ants', 'Indrek', 'Jaan', 'Jaanus',
                            'Jüri', 'Kristjan', 'Marek', 'Margus', 'Marko',
                            'Martin', 'Mati', 'Meelis', 'Mihkel', 'Peeter',
                            'Priit', 'Raivo', 'Rein', 'Sander', 'Siim', 'Tarmo',
                            'Tiit', 'Toomas', 'Tõnu', 'Urmas', 'Vello')

    first_names_female_est = ('Aino', 'Anna', 'Anne', 'Anneli', 'Anu', 'Diana',
                              'Ene', 'Eve', 'Kadri', 'Katrin', 'Kristi',
                              'Kristiina', 'Kristina', 'Laura', 'Linda', 'Maie',
                              'Malle', 'Mare', 'Maria', 'Marika', 'Merike',
                              'Niina', 'Piret', 'Reet', 'Riina', 'Sirje',
                              'Tiina', 'Tiiu', 'Triin', 'Ülle')

    first_names_est = first_names_male_est + first_names_female_est

    first_names_male_rus = ('Aleksander', 'Aleksandr', 'Aleksei', 'Alexander',
                            'Andrei', 'Artur', 'Dmitri', 'Igor', 'Ivan',
                            'Jevgeni', 'Juri', 'Maksim', 'Mihhail', 'Nikolai',
                            'Oleg', 'Pavel', 'Roman', 'Sergei', 'Sergey',
                            'Valeri', 'Viktor', 'Vladimir')

    first_names_female_rus = ('Aleksandra', 'Anna', 'Diana', 'Elena', 'Galina',
                              'Irina', 'Jekaterina', 'Jelena', 'Julia',
                              'Kristina', 'Ljubov', 'Ljudmila', 'Maria',
                              'Marina', 'Nadežda', 'Natalia', 'Natalja', 'Nina',
                              'Olga', 'Svetlana', 'Tamara', 'Tatiana',
                              'Tatjana', 'Valentina', 'Viktoria')

    first_names_rus = first_names_male_rus + first_names_female_rus

    first_names_male = set(first_names_male_est + first_names_male_rus)
    first_names_female = set(first_names_female_est + first_names_female_rus)
    first_names = first_names_male | first_names_female

    # http://ekspress.delfi.ee/kuum/\
    # top-500-eesti-koige-levinumad-perekonnanimed?id=27677149
    last_names_est = ('Aas', 'Aasa', 'Aasmäe', 'Aavik', 'Abel', 'Adamson',
                      'Ader', 'Alas', 'Allas', 'Allik', 'Anderson', 'Annus',
                      'Anton', 'Arro', 'Aru', 'Arula', 'Aun', 'Aus', 'Eller',
                      'Erik', 'Erm', 'Ernits', 'Gross', 'Hallik', 'Hansen',
                      'Hanson', 'Hein', 'Heinsalu', 'Heinsoo', 'Holm', 'Hunt',
                      'Härm', 'Ilves', 'Ivask', 'Jaakson', 'Jaanson', 'Jaanus',
                      'Jakobson', 'Jalakas', 'Johanson', 'Juhanson', 'Juhkam',
                      'Jänes', 'Järv', 'Järve', 'Jõe', 'Jõesaar', 'Jõgi',
                      'Jürgens', 'Jürgenson', 'Jürisson', 'Kaasik', 'Kadak',
                      'Kala', 'Kalamees', 'Kalda', 'Kaljula', 'Kaljurand',
                      'Kaljuste', 'Kaljuvee', 'Kallas', 'Kallaste', 'Kalm',
                      'Kalmus', 'Kangro', 'Kangur', 'Kapp', 'Karro', 'Karu',
                      'Kasak', 'Kase', 'Kasemaa', 'Kasemets', 'Kask', 'Kass',
                      'Kattai', 'Kaur', 'Kelder', 'Kesküla', 'Kiik', 'Kiil',
                      'Kiis', 'Kiisk', 'Kikas', 'Kikkas', 'Kilk', 'Kink',
                      'Kirs', 'Kirsipuu', 'Kirss', 'Kivi', 'Kivilo', 'Kivimäe',
                      'Kivistik', 'Klaas', 'Klein', 'Koger', 'Kohv', 'Koit',
                      'Koitla', 'Kokk', 'Kolk', 'Kont', 'Kool', 'Koort',
                      'Koppel', 'Korol', 'Kotkas', 'Kotov', 'Koval', 'Kozlov',
                      'Kriisa', 'Kroon', 'Krõlov', 'Kudrjavtsev', 'Kulikov',
                      'Kuningas', 'Kurg', 'Kurm', 'Kurvits', 'Kutsar', 'Kuus',
                      'Kuuse', 'Kuusik', 'Kuusk', 'Kärner', 'Käsper', 'Käär',
                      'Käärik', 'Kõiv', 'Kütt', 'Laan', 'Laane', 'Laanemets',
                      'Laas', 'Laht', 'Laine', 'Laks', 'Lang', 'Lass', 'Laur',
                      'Lauri', 'Lehiste', 'Leht', 'Lehtla', 'Lehtmets', 'Leis',
                      'Lember', 'Lepik', 'Lepp', 'Leppik', 'Liblik', 'Liiv',
                      'Liiva', 'Liivak', 'Liivamägi', 'Lill', 'Lillemets',
                      'Lind', 'Link', 'Lipp', 'Lokk', 'Lomp', 'Loorits', 'Luht',
                      'Luik', 'Lukin', 'Lukk', 'Lumi', 'Lumiste', 'Luts',
                      'Lätt', 'Lääne', 'Lääts', 'Lõhmus', 'Maasik', 'Madisson',
                      'Maidla', 'Mandel', 'Maripuu', 'Mark', 'Markus', 'Martin',
                      'Martinson', 'Meier', 'Meister', 'Melnik', 'Merila',
                      'Mets', 'Michelson', 'Mikk', 'Miller', 'Mitt', 'Moor',
                      'Muru', 'Must', 'Mäe', 'Mäeots', 'Mäesalu', 'Mägi',
                      'Mänd', 'Mändla', 'Männik', 'Männiste', 'Mõttus',
                      'Mölder', 'Mürk', 'Müür', 'Müürsepp', 'Niit', 'Nurk',
                      'Nurm', 'Nuut', 'Nõmm', 'Nõmme', 'Nõmmik', 'Oja', 'Ojala',
                      'Ojaste', 'Oks', 'Olesk', 'Oras', 'Orav', 'Org', 'Ots',
                      'Ott', 'Paal', 'Paap', 'Paas', 'Paju', 'Pajula', 'Palm',
                      'Palu', 'Parts', 'Pent', 'Peterson', 'Pettai', 'Pihelgas',
                      'Pihlak', 'Piho', 'Piir', 'Piirsalu', 'Pikk', 'Ploom',
                      'Poom', 'Post', 'Pruul', 'Pukk', 'Pulk', 'Puusepp',
                      'Pärn', 'Pärna', 'Pärnpuu', 'Pärtel', 'Põder', 'Põdra',
                      'Põld', 'Põldma', 'Põldmaa', 'Põllu', 'Püvi', 'Raadik',
                      'Raag', 'Raamat', 'Raid', 'Raidma', 'Raja', 'Rand',
                      'Randmaa', 'Randoja', 'Raud', 'Raudsepp', 'Rebane',
                      'Reimann', 'Reinsalu', 'Remmel', 'Rohtla', 'Roos',
                      'Roosileht', 'Roots', 'Rosenberg', 'Rosin', 'Ruus',
                      'Rätsep', 'Rüütel', 'Saar', 'Saare', 'Saks', 'Salu',
                      'Salumets', 'Salumäe', 'Sander', 'Sarap', 'Sarapuu',
                      'Sarv', 'Saul', 'Schmidt', 'Sepp', 'Sibul', 'Siim',
                      'Sikk', 'Sild', 'Sillaots', 'Sillaste', 'Silm', 'Simson',
                      'Sirel', 'Sisask', 'Sokk', 'Soo', 'Soon', 'Soosaar',
                      'Soosalu', 'Soots', 'Suits', 'Sulg', 'Susi', 'Sutt',
                      'Suur', 'Suvi', 'Säde', 'Sööt', 'Taal', 'Tali', 'Talts',
                      'Tamberg', 'Tamm', 'Tamme', 'Tammik', 'Teder', 'Teearu',
                      'Teesalu', 'Teras', 'Tiik', 'Tiits', 'Tilk', 'Tomingas',
                      'Tomson', 'Toom', 'Toome', 'Tooming', 'Toomsalu', 'Toots',
                      'Trei', 'Treial', 'Treier', 'Truu', 'Tuisk', 'Tuul',
                      'Tuulik', 'Täht', 'Tõnisson', 'Uibo', 'Unt', 'Urb', 'Uus',
                      'Uustalu', 'Vaher', 'Vaht', 'Vahter', 'Vahtra', 'Vain',
                      'Vaino', 'Valge', 'Valk', 'Vares', 'Varik', 'Veski',
                      'Viik', 'Viira', 'Viks', 'Vill', 'Villemson', 'Visnapuu',
                      'Vähi', 'Väli', 'Võsu', 'Õispuu', 'Õun', 'Õunapuu')

    last_names_rus = ('Abramov', 'Afanasjev', 'Aleksandrov', 'Alekseev',
                      'Andreev', 'Anissimov', 'Antonov', 'Baranov', 'Beljajev',
                      'Belov', 'Bogdanov', 'Bondarenko', 'Borissov', 'Bõstrov',
                      'Danilov', 'Davõdov', 'Denissov', 'Dmitriev', 'Drozdov',
                      'Egorov', 'Fedorov', 'Fedotov', 'Filatov', 'Filippov',
                      'Fjodorov', 'Fomin', 'Frolov', 'Gavrilov', 'Gerassimov',
                      'Golubev', 'Gontšarov', 'Gorbunov', 'Grigoriev', 'Gromov',
                      'Gusev', 'Ignatjev', 'Iljin', 'Ivanov', 'Jakovlev',
                      'Jefimov', 'Jegorov', 'Jermakov', 'Jeršov', 'Kalinin',
                      'Karpov', 'Karpov', 'Kazakov', 'Kirillov', 'Kisseljov',
                      'Klimov', 'Kolesnik', 'Komarov', 'Kondratjev',
                      'Konovalov', 'Konstantinov', 'Korol', 'Kostin', 'Kotov',
                      'Koval', 'Kozlov', 'Kruglov', 'Krõlov', 'Kudrjavtsev',
                      'Kulikov', 'Kuzmin', 'Kuznetsov', 'Lebedev', 'Loginov',
                      'Lukin', 'Makarov', 'Maksimov', 'Malõšev', 'Maslov',
                      'Matvejev', 'Medvedev', 'Melnik', 'Mihhailov', 'Miller',
                      'Mironov', 'Moroz', 'Naumov', 'Nazarov', 'Nikiforov',
                      'Nikitin', 'Nikolaev', 'Novikov', 'Orlov', 'Ossipov',
                      'Panov', 'Pavlov', 'Petrov', 'Poljakov', 'Popov',
                      'Romanov', 'Rosenberg', 'Rumjantsev', 'Safronov',
                      'Saveljev', 'Semenov', 'Sergejev', 'Sidorov', 'Smirnov',
                      'Sobolev', 'Sokolov', 'Solovjov', 'Sorokin', 'Stepanov',
                      'Suvorov', 'Tarassov', 'Tihhomirov', 'Timofejev', 'Titov',
                      'Trofimov', 'Tsvetkov', 'Vasiliev', 'Vinogradov',
                      'Vlassov', 'Volkov', 'Vorobjov', 'Voronin', 'Zahharov',
                      'Zaitsev', 'Zujev', 'Ševtšenko', 'Štšerbakov',
                      'Štšerbakov', 'Žukov', 'Žuravljov')
    last_names = set(last_names_est + last_names_rus)

    def first_name_male_est(self):
        return self.random_element(self.first_names_male_est)

    def first_name_female_est(self):
        return self.random_element(self.first_names_female_est)

    def first_name_male_rus(self):
        return self.random_element(self.first_names_male_rus)

    def first_name_female_rus(self):
        return self.random_element(self.first_names_female_rus)

    def first_name_est(self):
        return self.random_element(self.first_names_est)

    def first_name_rus(self):
        return self.random_element(self.first_names_rus)

    def last_name_est(self):
        return self.random_element(self.last_names_est)

    def last_name_rus(self):
        return self.random_element(self.last_names_rus)
