# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):
    cities = (
        'Warszawa', 'Kraków', 'Łódź', 'Wrocław', 'Poznań', 'Gdańsk',
        'Szczecin',
        'Bydgoszcz', 'Lublin', 'Katowice', 'Białystok', 'Gdynia',
        'Częstochowa', 'Radom', 'Sosnowiec', 'Toruń', 'Kielce', 'Gliwice',
        'Rzeszów', 'Zabrze', 'Bytom', 'Olsztyn', 'Bielsko-Biała',
        'Ruda Śląska',
        'Rybnik', 'Tychy', 'Dąbrowa Górnicza', 'Gorzów Wielkopolski',
        'Elbląg',
        'Płock', 'Opole', 'Wałbrzych', 'Zielona Góra', 'Włocławek', 'Tarnów',
        'Chorzów', 'Koszalin', 'Kalisz', 'Legnica', 'Grudziądz', 'Słupsk',
        'Jaworzno', 'Jastrzębie-Zdrój', 'Nowy Sącz', 'Jelenia Góra', 'Konin',
        'Piotrków Trybunalski', 'Siedlce', 'Inowrocław', 'Mysłowice', 'Piła',
        'Lubin', 'Ostrów Wielkopolski', 'Ostrowiec Świętokrzyski', 'Gniezno',
        'Stargard Szczeciński', 'Siemianowice Śląskie', 'Suwałki', 'Głogów',
        'Pabianice', 'Chełm', 'Zamość', 'Tomaszów Mazowiecki', 'Leszno',
        'Przemyśl', 'Stalowa Wola', 'Kędzierzyn-Koźle', 'Łomża', 'Żory',
        'Mielec', 'Tarnowskie Góry', 'Tczew', 'Bełchatów', 'Świdnica',
        'Ełk', 'Pruszków', 'Będzin', 'Biała Podlaska', 'Zgierz',
        'Piekary Śląskie', 'Racibórz', 'Legionowo', 'Ostrołęka',
        'Świętochłowice', 'Starachowice', 'Zawiercie', 'Wejherowo',
        'Puławy', 'Wodzisław Śląski', 'Starogard Gdański', 'Skierniewice',
        'Tarnobrzeg', 'Skarżysko-Kamienna', 'Radomsko', 'Krosno', 'Rumia',
        'Dębica', 'Kołobrzeg', 'Kutno', 'Nysa', 'Ciechanów', 'Otwock',
        'Piaseczno', 'Zduńska Wola', 'Sieradz', 'Świnoujście', 'Żyrardów',
        'Szczecinek', 'Świdnik', 'Chojnice', 'Nowa Sól', 'Oświęcim',
        'Bolesławiec', 'Mińsk Mazowiecki', 'Mikołów', 'Jarosław', 'Sanok',
        'Knurów', 'Malbork', 'Żary', 'Kwidzyn', 'Chrzanów', 'Sopot',
        'Sochaczew', 'Wołomin', 'Oleśnica', 'Brzeg', 'Olkusz', 'Jasło',
        'Cieszyn', 'Kraśnik', 'Lębork', 'Czechowice-Dziedzice', 'Dzierżoniów',
        'Ostróda', 'Police', 'Nowy Targ', 'Iława', 'Czeladź', 'Myszków',
        'Żywiec', 'Zgorzelec', 'Oława', 'Bielawa', 'Swarzędz', 'Mława',
        'Ząbki', 'Łuków', 'Augustów', 'Śrem', 'Bochnia', 'Luboń', 'Giżycko',
        'Grodzisk Mazowiecki', 'Łowicz', 'Krotoszyn', 'Września',
        'Turek', 'Pruszcz Gdański', 'Brodnica', 'Gorlice',
        'Czerwionka-Leszczyny', 'Kłodzko', 'Marki', 'Nowy Dwór Mazowiecki',
        'Kętrzyn', 'Zakopane', 'Wyszków', 'Biłgoraj', 'Żagań',
        'Bielsk Podlaski', 'Świecie', 'Wałcz', 'Jarocin', 'Pszczyna',
        'Wągrowiec', 'Szczytno', 'Białogard', 'Sandomierz', 'Bartoszyce',
        'Kluczbork', 'Lubliniec', 'Skawina', 'Jawor', 'Kościan', 'Wieluń',
        'Kościerzyna', 'Nowa Ruda', 'Świebodzice', 'Koło', 'Piastów',
        'Goleniów', 'Ostrów Mazowiecka', 'Polkowice', 'Lubartów', 'Zambrów',
        'Płońsk', 'Reda', 'Łaziska Górne', 'Środa Wielkopolska',
    )

    street_prefixes = (
        'ulica', 'aleja', 'plac',
    )

    streets = (
        'Polna', 'Leśna', 'Słoneczna', 'Krótka', 'Szkolna', 'Ogrodowa',
        'Lipowa', 'Brzozowa', 'Łąkowa', 'Kwiatowa', 'Sosnowa', 'Kościelna',
        'Akacjowa', 'Parkowa', 'Zielona', 'Kolejowa', 'Sportowa', 'Dębowa',
        'Kościuszki', 'Maja', 'Mickiewicza', 'Cicha', 'Spokojna', 'Klonowa',
        'Spacerowa', 'Swierkowa', 'Kasztanowa', 'Nowa', 'Piaskowa',
        'Sienkiewicza', 'Rózana', 'Topolowa', 'Wiśniowa', 'Dworcowa',
        'Wiejska', 'Graniczna', 'Słowackiego', 'Długa', 'Wrzosowa',
        'Konopnickiej', 'Boczna', 'Wąska', 'Wierzbowa', 'Jaśminowa',
        'Wspólna', 'Modrzewiowa', 'Kopernika', 'Jana Pawła II',
        'Poprzeczna', 'Wesoła', 'Pogodna', 'Żeromskiego', 'Rynek', 'Bukowa',
        'Wojska Polskiego', 'Sadowa', 'Górna', 'Jodłowa', 'Wolności',
        'Glówna', 'Młyńska', 'Strażacka', 'Prusa', 'Jesionowa', 'Przemysłowa',
        'Osiedlowa', 'Wiosenna', 'Sikorskiego', 'Chopina', 'Południowa',
        'Malinowa', 'Stawowa', 'Reymonta', 'Piłsudskiego', 'Zacisze',
        'Cmentarna', 'Okrężna', 'Kochanowskiego', 'Armii Krajowej', 'Miła',
        'Jasna', 'Wodna', 'Zamkowa', 'Witosa', 'Reja', 'Warszawska',
        'Miodowa', 'Partyzantów', 'Krzywa', 'Kilińskiego', 'Dolna',
        'Podgórna', 'Kreta', 'Jarzębinowa', 'Moniuszki', 'Targowa', 'Prosta',
        'Orzeszkowej', 'Spółdzielcza', 'Jagodowa', 'Działkowa', 'Staszica',
        'Orzechowa', 'Rzemieślnicza', 'Rzeczna', 'Bolesława Chrobrego',
        'Fabryczna', 'Tęczowa', 'Chabrowa', 'Poziomkowa', 'Konwaliowa',
        'Wyszyńskiego', 'Kalinowa', 'Północna', 'Matejki', 'Grunwaldzka',
        'Cisowa', 'Nadrzeczna', 'Pocztowa', 'Zachodnia', 'Dąbrowskiego',
        'Grabowa', 'Norwida', 'Źródlana', 'Asnyka', 'Gajowa', 'Paderewskiego',
        'Listopada', 'Wyspiańskiego', 'Mostowa', 'Broniewskiego', 'Tuwima',
        'Wschodnia', 'Jaworowa', 'Poznańska', 'Makowa', 'Bema', 'Jeziorna',
        'Piękna', 'Czereśniowa', 'Mała', 'Krakowska', 'Radosna',
        'Leszczynowa', 'Traugutta', 'Jadwigi', 'Rolna', 'Wyzwolenia',
        'Piastowska', 'Grzybowa', 'Krasickiego', 'Podleśna', 'Żytnia',
        'Złota', 'Bursztynowa', 'Żwirowa', 'Stycznia', 'Widokowa',
        'Kazimierza Wielkiego', 'Kamienna', 'Jałowcowa', 'Morelowa',
        'Mieszka I', 'Myśliwska', 'Łączna', 'Szpitalna', 'Wczasowa',
        'Żurawia', 'Fiołkowa', 'Głowackiego', 'Rolnicza', 'Tulipanowa',
        'Władysława Jagiełły', 'Dworska', 'Letnia', 'Liliowa', 'Owocowa',
        'Pułaskiego', 'Stefana Batorego', 'Harcerska', 'Kołłątaja',
        'Strzelecka', 'Kraszewskiego', 'Władysława Łokietka',
        'Żwirki i Wigury', 'Wrocławska', 'Gdańska', 'Turystyczna',
        'Niepodległości', 'Poniatowskiego', 'Korczaka', 'Rybacka',
        'Narutowicza', 'Okrzei', 'Krucza', 'Jagiellońska', 'Świerczewskiego',
        'Kasprowicza', 'Szeroka', 'Jana III Sobieskiego', 'Młynarska',
        'Olchowa', 'Powstańców Śląskich', 'Rumiankowa', 'Stroma',
        'Starowiejska', 'Mazowiecka',
        'Lawendowa', 'Robotnicza', 'Zbożowa', 'Mokra',
        'Powstańców Wielkopolskich', 'Towarowa', 'Dobra', 'Środkowa',
        'Willowa', 'Zielna', 'Zdrojowa', 'Opolska', 'Agrestowa', 'Księżycowa',
        'Zwycięstwa', 'Fredry', 'Letniskowa', 'Andersa', 'Baczynskiego',
        'Batalionów Chłopskich', 'Dąbrowskiej', 'Orla', 'Skłodowskiej-Curie',
        'Błękitna', 'Rubinowa', 'Brzoskwiniowa', 'Urocza', 'Gałczynskiego',
        'Krasińskiego', 'Pomorska', 'Szymanowskiego', 'Jeżynowa',
        'Czarnieckiego', 'Nałkowskiej', 'Zaciszna', 'Porzeczkowa',
        'Krańcowa', 'Jesienna', 'Klasztorna', 'Irysowa', 'Niecała',
        'Wybickiego', 'Nadbrzeżna', 'Szarych Szeregów', 'Wałowa',
        'Słowicza', 'Strumykowa', 'Drzymały', 'Gołębia', 'Torowa',
        'Cegielniana', 'Cyprysowa', 'Słowianska', 'Diamentowa', 'Waryńskiego',
        'Częstochowska', 'Dojazdowa', 'Przechodnia', 'Hallera', 'Lubelska',
        'Plater', 'Popiełuszki', 'Borówkowa', 'Chełmońskiego', 'Daszyńskiego',
        'Plażowa', 'Tartaczna', 'Jabłoniowa', 'Kossaka', 'Skargi', 'Ludowa',
        'Sokola', 'Azaliowa', 'Szmaragdowa', 'Lipca', 'Staffa', 'Tysiąclecia',
        'Brzechwy', 'Jastrzębia', 'Kusocińskiego', 'Storczykowa', 'Wilcza',
        'Górnicza', 'Szafirowa', 'Długosza', 'Handlowa', 'Krokusowa',
        'Składowa', 'Widok', 'Perłowa', 'Skośna', 'Wypoczynkowa', 'Chmielna',
        'Jaskółcza', 'Nowowiejska', 'Piwna', 'Śląska', 'Zaułek', 'Głogowa',
        'Górska', 'Truskawkowa', 'Kaszubska', 'Kosynierów', 'Mazurska',
        'Srebrna', 'Bociania', 'Ptasia', 'Cedrowa', 'Rycerska',
        'Wieniawskiego', 'Żabia', 'Toruńska', 'Podmiejska', 'Słonecznikowa',
        'Sowia', 'Stolarska', 'Powstańców', 'Sucharskiego',
        'Bolesława Krzywoustego', 'Konarskiego',
        'Szczęśliwa', 'Lazurowa', 'Miarki', 'Narcyzowa', 'Browarna',
        'Konstytucji 3 Maja', 'Majowa', 'Miłosza', 'Malczewskiego', 'Orkana',
        'Skrajna', 'Bankowa', 'Bydgoska', 'Piekarska', 'Żeglarska', 'Jana',
        'Turkusowa', 'Tylna', 'Wysoka', 'Zakątek', 'Maczka', 'Morska',
        'Rataja', 'Szewska', 'Podwale', 'Pałacowa', 'Magnoliowa', 'Ceglana',
        'Sawickiej', 'Ściegiennego', 'Wiklinowa', 'Zakole', 'Borowa',
        'Kolorowa', 'Lisia', 'Lotnicza', 'Sarnia', 'Wiązowa', 'Grottgera',
        'Kolonia', 'Królewska', 'Promienna', 'Daleka', 'Jana Sobieskiego',
        'Rejtana', 'Wiatraczna', 'Kaliska', 'Łanowa', 'Średnia', 'Wiślana',
        'Wróblewskiego', 'Koralowa', 'Kruczkowskiego', 'Lelewela',
        'Makuszyńskiego', 'Sybiraków', 'Kowalska', 'Morcinka', 'Odrzańska',
        'Okulickiego', 'Solidarnosci', 'Zapolskiej', 'Łabędzia', 'Wojciecha',
        'Bałtycka', 'Lwowska', 'Rajska', 'Korfantego', 'Pszenna', 'Ciasna',
        'Floriana', 'Hutnicza', 'Kielecka',
    )

    regions = (
        "Dolnośląskie", "Kujawsko - pomorskie", "Lubelskie", "Lubuskie",
        "Łódzkie", "Małopolskie", "Mazowieckie", "Opolskie", "Podkarpackie",
        "Podlaskie", "Pomorskie", "Śląskie", "Świętokrzyskie",
        "Warmińsko - mazurskie", "Wielkopolskie", "Zachodniopomorskie",
    )

    building_number_formats = ('##', '###', "##/##")
    postcode_formats = ('##-###',)
    street_address_formats = (
        '{{street_prefix}} {{street_name}} {{building_number}}',
        '{{street_prefix_short}} {{street_name}} {{building_number}}',
    )
    address_formats = (
        "{{street_address}}\n{{postcode}} {{city}}",
    )

    def street_prefix(self):
        """
        Randomly returns a street prefix
        :example 'aleja'
        """
        return self.random_element(self.street_prefixes)

    def street_prefix_short(self):
        """
        Randomly returns an abbreviation of the street prefix.
        :example 'al.'
        """
        return self.random_element(self.street_prefixes)[:2] + '.'

    def street_name(self):
        """
        Randomly returns a street name
        :example 'Wróblewskiego'
        """
        return self.random_element(self.streets)

    def city(self):
        """
        Randomly returns a street name
        :example 'Konin'
        """
        return self.random_element(self.cities)

    def region(self):
        """
        :example 'Wielkopolskie'
        """
        return self.random_element(self.regions)
