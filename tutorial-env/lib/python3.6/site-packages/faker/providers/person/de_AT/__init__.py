# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as PersonProvider


class Provider(PersonProvider):
    formats = (
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{prefix}} {{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{prefix}} {{first_name}} {{last_name}}',
    )
    first_names = (
        'Alexander', 'Alina', 'Andreas', 'Anna', 'Anton',
        'Benjamin', 'Bernhard',
        'Christian', 'Christop',
        'Daniel', 'David', 'Dominik',
        'Elena', 'Elias', 'Emil', 'Emilia',
        'Fabian', 'Felix', 'Florian', 'Franz', 'Fransizka',
        'Gabriel', 'Gernot',
        'Hanna',
        'Ingrid', 'Isabel',
        'Jakob', 'Jana', 'Jasmin', 'Johanna', 'Johannes', 'Jonas', 'Julia', 'Julian',
        'Katharinna', 'Konrad', 'Konstantin',
        'Lara', 'Laura', 'Lena', 'Leo', 'Leon', 'Linda', 'Luca', 'Lukas',
        'Marcel', 'Maria', 'Martin', 'Matthias', 'Max', 'Maximilian', 'Mia', 'Michael', 'Moritz',
        'Nico', 'Niklas', 'Nina', 'Noah',
        'Oliver', 'Olivia',
        'Paul', 'Paula', 'Philipp', 'Pia',
        'Raphael', 'Robert',
        'Samuel', 'Sarah', 'Sebastian', 'Simon', 'Sophie',
        'Theresa', 'Thomas', 'Tim',
        'Tobias',
        'Valentin',
    )
    last_names = (
        'Auer', 'Aigner',
        'Bauer', 'Baumgartner', 'Berger', 'Binder', 'Brunner',
        'Cap', 'Capek', 'Cech', 'Chum',
        'Deng', 'Denk', 'Daume', 'Dienstl',
        'Ebner', 'Eder', 'Egger',
        'Fasching', 'Felber', 'Ferstel', 'Fichtner', 'Fischer', 'Fuchs',
        'Gasser', 'Gastegger', 'Geier', 'Geisler', 'Grabner', 'Gruber',
        'Haas', 'Haiden', 'Hofer', 'Holzer', 'Huber',
        'Illes', 'Ircher', 'Itzlinger',
        'Jahn', 'Jobst', 'Jung', 'Jungbauer', 'Just',
        'Kainz', 'Karl', 'Karner', 'Koller',
        'Lang', 'Lechner', 'Lehner', 'Leitner',
        'Maier', 'Mair', 'Maurer', 'Mayer', 'Mayr', 'Moser', 'Müllner',
        'Pichler', 'Pucher',
        'Reiter', 'Riegler',
        'Schmid', 'Schneider', 'Schuster', 'Schwarz', 'Stadler', 'Steiner',
        'Wallner', 'Weber', 'Weiss', 'Wieser', 'Wimmer', 'Winkler', 'Winter', 'Wolf',
    )

    prefixes = ('Dr.', 'Mag.', 'Ing.', 'Dipl.-Ing.', 'Prof.', 'Univ.Prof.')
