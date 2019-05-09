human_data = {}
droid_data = {}


def setup():
    from .schema import Human, Droid

    global human_data, droid_data
    luke = Human(
        id="1000",
        name="Luke Skywalker",
        friends=["1002", "1003", "2000", "2001"],
        appears_in=[4, 5, 6],
        home_planet="Tatooine",
    )

    vader = Human(
        id="1001",
        name="Darth Vader",
        friends=["1004"],
        appears_in=[4, 5, 6],
        home_planet="Tatooine",
    )

    han = Human(
        id="1002",
        name="Han Solo",
        friends=["1000", "1003", "2001"],
        appears_in=[4, 5, 6],
        home_planet=None,
    )

    leia = Human(
        id="1003",
        name="Leia Organa",
        friends=["1000", "1002", "2000", "2001"],
        appears_in=[4, 5, 6],
        home_planet="Alderaan",
    )

    tarkin = Human(
        id="1004",
        name="Wilhuff Tarkin",
        friends=["1001"],
        appears_in=[4],
        home_planet=None,
    )

    human_data = {
        "1000": luke,
        "1001": vader,
        "1002": han,
        "1003": leia,
        "1004": tarkin,
    }

    c3po = Droid(
        id="2000",
        name="C-3PO",
        friends=["1000", "1002", "1003", "2001"],
        appears_in=[4, 5, 6],
        primary_function="Protocol",
    )

    r2d2 = Droid(
        id="2001",
        name="R2-D2",
        friends=["1000", "1002", "1003"],
        appears_in=[4, 5, 6],
        primary_function="Astromech",
    )

    droid_data = {"2000": c3po, "2001": r2d2}


def get_character(id):
    return human_data.get(id) or droid_data.get(id)


def get_friends(character):
    return map(get_character, character.friends)


def get_hero(episode):
    if episode == 5:
        return human_data["1000"]
    return droid_data["2001"]


def get_human(id):
    return human_data.get(id)


def get_droid(id):
    return droid_data.get(id)
