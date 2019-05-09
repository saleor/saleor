# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as PersonProvider


class Provider(PersonProvider):
    formats = (
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{last_name}}, {{first_name}}',
    )

    first_names = (
        'Tomas', 'Lukas', 'Mantas', 'Deividas', 'Arnas', 'Artūras',
        'Karolis', 'Dovydas', 'Dominykas', 'Darius', 'Edvinas', 'Jonas',
        'Martynas', 'Kajus', 'Donatas', 'Andrius', 'Matas', 'Rokas',
        'Augustas', 'Danielius', 'Mindaugas', 'Paulius', 'Marius',
        'Armandas', 'Edgaras', 'Jokūbas', 'Nedas', 'Tadas', 'Nerijus',
        'Simonas', 'Vytautas', 'Artūras', 'Robertas', 'Eimantas', 'Arijus',
        'Nojus', 'Egidijus', 'Aurimas', 'Emilis', 'Laurynas', 'Edvardas',
        'Joris', 'Pijus', 'Erikas', 'Domas', 'Vilius', 'Evaldas', 'Justinas',
        'Aleksandras', 'Kristupas', 'Gabrielius', 'Benas', 'Gytis', 'Arminas',
        'Vakris', 'Tautvydas', 'Domantas', 'Justas', 'Markas', 'Antanas',
        'Arūnas', 'Ernestas', 'Aronas', 'Vaidas', 'Ąžuolas', 'Titas', 'Giedrius',
        'Ignas', 'Povilas', 'Saulius', 'Julius', 'Arvydas', 'Kęstutis', 'Rytis',
        'Aistis', 'Gediminas', 'Algirdas', 'Naglis', 'Irmantas', 'Rolandas',
        'Aivaras', 'Simas', 'Faustas', 'Ramūnas', 'Šarūnas', 'Gustas', 'Tajus',
        'Dainius', 'Arnoldas', 'Linas', 'Rojus', 'Adomas', 'Žygimantas',
        'Ričardas', 'Orestas', 'Kipras', 'Juozas', 'Audrius', 'Romualdas',
        'Petras', 'Eleonora', 'Raminta', 'Dovilė', 'Sandra', 'Dominyka', 'Ana',
        'Erika', 'Kristina', 'Gintarė', 'Rūta', 'Edita', 'Karina', 'Živilė',
        'Jolanta', 'Radvilė', 'Ramunė', 'Svetlana', 'Ugnė', 'Eglė', 'Viktorija',
        'Justina', 'Brigita', 'Rasa', 'Marija', 'Giedrė', 'Iveta', 'Sonata',
        'Vitalija', 'Adrija', 'Goda', 'Paulina', 'Kornelija', 'Liepa', 'Vakarė',
        'Milda', 'Meda', 'Vaida', 'Izabelė', 'Jovita', 'Irma', 'Žemyna', 'Leila',
        'Rimantė', 'Mantė', 'Rytė', 'Perla', 'Greta', 'Monika', 'Ieva', 'Indrė',
        'Ema', 'Aurelija', 'Smiltė', 'Ingrida', 'Simona', 'Amelija', 'Sigita',
        'Olivija', 'Laurita', 'Jorūnė', 'Leticija', 'Vigilija', 'Medėja', 'Laura',
        'Agnė', 'Evelina', 'Kotryna', 'Lėja', 'Aušra', 'Neringa', 'Gerda',
        'Jurgita', 'Rusnė', 'Aušrinė', 'Rita', 'Elena', 'Ineta', 'Ligita',
        'Vasarė', 'Vėjūnė', 'Ignė', 'Gytė', 'Ariana', 'Arielė', 'Vytė', 'Eidvilė',
        'Karolina', 'Miglė', 'Viltė', 'Jolanta', 'Enrika', 'Aurėja', 'Vanesa',
        'Darija', 'Reda', 'Milana', 'Rugilė', 'Diana',
    )

    last_names = (
        'Kazlauskas', 'Jankauskas', 'Petrauskas', 'Pocius', 'Stankevičius',
        'Vsiliauskas', 'Žukauskas', 'Butkus', 'Paulauskas', 'Urbonas',
        'Kavaliauskas', 'Sakalauskas', 'Žukauskas', 'Akelis', 'Ambrasas',
        'Kairys', 'Kalvaitis', 'Kalvelis', 'Kalvėnas', 'Kaupas', 'Kiška',
        'Gagys', 'Gailius', 'Gailys', 'Gaižauskas', 'Gaičiūnas', 'Galdikas',
        'Gintalas', 'Ginzburgas', 'Grinius', 'Gronskis', 'Nagys', 'Naujokas',
        'Narušis', 'Nausėda', 'Poška', 'Povilonis',
    )
