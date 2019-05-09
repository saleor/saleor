# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as PersonProvider


class Provider(PersonProvider):
    formats = (
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{last_name}}-{{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{last_name}}-{{last_name}}',
        '{{prefix_male}} {{first_name_male}} {{last_name}}',
        '{{prefix_female}} {{first_name_female}} {{last_name}}',
        '{{prefix_male}} {{first_name_male}} {{last_name}}',
        '{{prefix_female}} {{first_name_female}} {{last_name}}',
    )

    first_names_male = (
        'Adam', 'Albert', 'Aksel', 'Alex', 'Alexander', 'Alf', 'Allan',
        'Alvin', 'Anders', 'André', 'Andreas', 'Anton', 'Arne', 'Asger',
        'ugust', 'Benjamin', 'Benny', 'Bent', 'Bertil', 'Bertram', 'Birger',
        'Bjarne', 'Bo', 'Bob', 'Bobby', 'Boe', 'Boris', 'Borris',
        'Brian', 'Bruno', 'Bøje', 'Børge', 'Carl', 'Carlo', 'Carsten',
        'Casper', 'Christian', 'Christoffer', 'Christopher', 'Claus', 'Clavs', 'Curt',
        'Dan', 'Daniel', 'Danny', 'David', 'Dennis', 'Ebbe', 'Einar',
        'Einer', 'Elias', 'Emil', 'Eric', 'Erik', 'Erling', 'Ernst',
        'Esben', 'Finn', 'Flemming', 'Frank', 'Frans', 'Freddy', 'Frede',
        'Frederik', 'Frode', 'Georg', 'George', 'Gert', 'Gorm', 'Gunnar',
        'Gunner', 'Gustav', 'Hans', 'Helge', 'Henrik', 'Henry', 'Herbert',
        'Herman', 'Hjalte', 'Holger', 'Hugo', 'Ib', 'Ivan', 'Iver',
        'Jack', 'Jacob', 'Jakob', 'James', 'Jan', 'Jano', 'Jarl',
        'Jean', 'Jens', 'Jeppe', 'Jesper', 'Jim', 'Jimmy', 'Joachim',
        'Joakim', 'Johan', 'Johannes', 'John', 'Johnnie', 'Johnny', 'Jon',
        'Jonas', 'Jonathan', 'Julius', 'Jørgen', 'Karl', 'Karlo', 'Karsten',
        'Kaspar', 'Kasper', 'Keld', 'Ken', 'Kenn', 'Kenneth', 'Kenny',
        'Kent', 'Kim', 'Kjeld', 'Klaus', 'Klavs', 'Kristian', 'Kurt',
        'Kåre', 'Lars', 'Lasse', 'Laurits', 'Laus', 'Laust', 'Leif',
        'Lennarth', 'Lucas', 'Ludvig', 'Mads', 'Magnus', 'Malthe', 'Marcus',
        'Marius', 'Mark', 'Martin', 'Mathias', 'Matthias', 'Michael', 'Mik',
        'Mikael', 'Mike', 'Mikkel', 'Mogens', 'Morten', 'Nick', 'Nicklas',
        'Nicolai', 'Nicolaj', 'Niels', 'Nikolai', 'Nikolaj', 'Nils', 'Noah',
        'Ole', 'Olfert', 'Oliver', 'Oscar', 'Oskar', 'Osvald', 'Otto',
        'Ove', 'Palle', 'Patrick', 'Paw', 'Peder', 'Per', 'Pete',
        'Peter', 'Paul', 'Philip', 'Poul', 'Preben', 'Ragnar', 'Ragner',
        'Rasmus', 'René', 'Richard', 'Richardt', 'Robert', 'Robin', 'Rolf',
        'Ron', 'Ronni', 'Ronnie', 'Ronny', 'Ruben', 'Rune', 'Sam',
        'Sebastian', 'Silas', 'Simon', 'Simon', 'Sonny', 'Steen', 'Stefan',
        'Sten', 'Stephan', 'Steve', 'Steven', 'Stig', 'Svenning', 'Søren',
        'Tage', 'Tejs', 'Thomas', 'Tim', 'Timmy', 'Tobias', 'Tom',
        'Tommy', 'Tonny', 'Torben', 'Troels', 'Uffe', 'Ulf', 'Ulrik',
        'Vagn', 'Valdemar', 'Verner', 'Victor', 'Villads', 'Werner', 'William',
        'Yan', 'Yannick', 'Yngve', 'Zacharias', 'Ziggy', 'Øivind', 'Øjvind',
        'Ørni', 'Øvli', 'Øystein', 'Øyvind', 'Åbjørn', 'Aage', 'Åge',
    )

    first_names_female = (
        'Abelone', 'Agnes', 'Agnete', 'Alberte', 'Alma', 'Amalie', 'Amanda',
        'Andrea', 'Ane', 'Anette', 'Anna', 'Anne', 'Annemette', 'Annette',
        'Asta', 'Astrid', 'Benedicte', 'Benedikte', 'Bente', 'Benthe', 'Berit',
        'Berta', 'Beth', 'Bettina', 'Birgit', 'Birgitte', 'Birte', 'Birthe',
        'Bitten', 'Bodil', 'Britt', 'Britta', 'Camilla', 'Carina', 'Carla',
        'Caroline', 'Cathrine', 'Catrine', 'Cecilie', 'Charlotte', 'Christina', 'Christine',
        'Cirkeline', 'Clara', 'Connie', 'Conny', 'Dagmar', 'Dagny', 'Daniella',
        'Dina', 'Ditte', 'Doris', 'Dorte', 'Dorthe', 'Edith', 'Elin',
        'Elisabeth', 'Ella', 'Ellen', 'Elna', 'Else', 'Elsebeth', 'Emilie',
        'Emily', 'Emma', 'Erna', 'Esmarelda', 'Ester', 'Filippa', 'Frederikke',
        'Freja', 'Frida', 'Gerda', 'Gertrud', 'Gitte', 'Grete', 'Grethe',
        'Gundhild', 'Gunhild', 'Gurli', 'Gyda', 'Hannah', 'Hanne', 'Heidi',
        'Helen', 'Helle', 'Henriette', 'Herdis', 'Iben', 'Ida', 'Inga',
        'Inge', 'Ingelise', 'Inger', 'Ingrid', 'Irma', 'Isabella', 'Jacobine',
        'Jacqueline', 'Janne', 'Janni', 'Jannie', 'Jasmin', 'Jean', 'Jenny',
        'Joan', 'Johanne', 'Jonna', 'Josefine', 'Josephine', 'Julie', 'Justina',
        'Jytte', 'Karen', 'Karin', 'Karina', 'Karla', 'Karoline', 'Katcha',
        'Katja', 'Katrine', 'Kirsten', 'Kirstin', 'Kirstine', 'Klara', 'Kristina',
        'Kristine', 'Laura', 'Lea', 'Lena', 'Lene', 'Leonora', 'Line',
        'Liva', 'Lona', 'Lone', 'Lotte', 'Louise', 'Lærke', 'Maiken',
        'Maja', 'Majken', 'Malene', 'Malou', 'Maren', 'Margit', 'Margrethe',
        'Maria', 'Marianne', 'Marie', 'Marlene', 'Mathilde', 'Maya', 'Merete',
        'Merethe', 'Mette', 'Mia', 'Michala', 'Michelle', 'Mie', 'Mille',
        'Mimi', 'Minna', 'Nadia', 'Naja', 'Nana', 'Nanna', 'Nanni',
        'Natasha', 'Natasja', 'Nete', 'Nicoline', 'Nina', 'Nora', 'Oda',
        'Odeline', 'Odette', 'Ofelia', 'Olga', 'Olivia', 'Patricia', 'Paula',
        'Paulina', 'Pernille', 'Pia', 'Ragna', 'Ragnhild', 'Randi', 'Rebecca',
        'Regitse', 'Regitze', 'Rikke', 'Rita', 'Ritt', 'Ronja', 'Rosa',
        'Ruth', 'Sabine', 'Sandra', 'Sanne', 'Sara', 'Sarah', 'Selma',
        'Signe', 'Sigrid', 'Silje', 'Sille', 'Simone', 'Sine', 'Sofia',
        'Sofie', 'Solveig', 'Solvej', 'Sonja', 'Sophie', 'Stina', 'Stine',
        'Susanne', 'Sussanne', 'Sussie', 'Sys', 'Sørine', 'Søs', 'Tammy',
        'Tanja', 'Thea', 'Tilde', 'Tina', 'Tine', 'Tove', 'Trine',
        'Ulla', 'Ulrike', 'Ursula', 'Vera', 'Victoria', 'Viola', 'Vivian',
        'Weena', 'Winni', 'Winnie', 'Xenia', 'Yasmin', 'Yda', 'Yrsa',
        'Yvonne', 'Zahra', 'Zara', 'Zehnia', 'Zelma', 'Zenia', 'Åse',
    )

    first_names = first_names_male + first_names_female

    last_names = (
        'Jensen', 'Nielsen', 'Hansen', 'Pedersen', 'Andersen', 'Christensen', 'Larsen',
        'Sørensen', 'Rasmussen', 'Petersen', 'Jørgensen', 'Madsen', 'Kristensen', 'Olsen',
        'Christiansen', 'Thomsen', 'Poulsen', 'Johansen', 'Knudsen', 'Mortensen', 'Møller',
        'Jacobsen', 'Jakobsen', 'Olesen', 'Frederiksen', 'Mikkelsen', 'Henriksen', 'Laursen',
        'Lund', 'Schmidt', 'Eriksen', 'Holm', 'Kristiansen', 'Clausen', 'Simonsen',
        'Svendsen', 'Andreasen', 'Iversen', 'Jeppesen', 'Mogensen', 'Jespersen', 'Nissen',
        'Lauridsen', 'Frandsen', 'Østergaard', 'Jepsen', 'Kjær', 'Carlsen', 'Vestergaard',
        'Jessen', 'Nørgaard', 'Dahl', 'Christoffersen', 'Skov', 'Søndergaard', 'Bertelsen',
        'Bruun', 'Lassen', 'Bach', 'Gregersen', 'Friis', 'Johnsen', 'Steffensen',
        'Kjeldsen', 'Bech', 'Krogh', 'Lauritsen', 'Danielsen', 'Mathiesen', 'Andresen',
        'Brandt', 'Winther', 'Toft', 'Ravn', 'Mathiasen', 'Dam', 'Holst',
        'Nilsson', 'Lind', 'Berg', 'Schou', 'Overgaard', 'Kristoffersen', 'Schultz',
        'Klausen', 'Karlsen', 'Paulsen', 'Hermansen', 'Thorsen', 'Koch', 'Thygesen',
    )

    prefixes_male = (
        'Hr', 'Dr.', 'Prof.', 'Univ.Prof.',
    )

    prefixes_female = (
        'Fru', 'Dr.', 'Prof.', 'Univ.Prof.',
    )
