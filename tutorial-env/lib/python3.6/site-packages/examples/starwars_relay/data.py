data = {}


def setup():
    global data

    from .schema import Ship, Faction

    xwing = Ship(id="1", name="X-Wing")

    ywing = Ship(id="2", name="Y-Wing")

    awing = Ship(id="3", name="A-Wing")

    # Yeah, technically it's Corellian. But it flew in the service of the rebels,
    # so for the purposes of this demo it's a rebel ship.
    falcon = Ship(id="4", name="Millenium Falcon")

    homeOne = Ship(id="5", name="Home One")

    tieFighter = Ship(id="6", name="TIE Fighter")

    tieInterceptor = Ship(id="7", name="TIE Interceptor")

    executor = Ship(id="8", name="Executor")

    rebels = Faction(
        id="1", name="Alliance to Restore the Republic", ships=["1", "2", "3", "4", "5"]
    )

    empire = Faction(id="2", name="Galactic Empire", ships=["6", "7", "8"])

    data = {
        "Faction": {"1": rebels, "2": empire},
        "Ship": {
            "1": xwing,
            "2": ywing,
            "3": awing,
            "4": falcon,
            "5": homeOne,
            "6": tieFighter,
            "7": tieInterceptor,
            "8": executor,
        },
    }


def create_ship(ship_name, faction_id):
    from .schema import Ship

    next_ship = len(data["Ship"].keys()) + 1
    new_ship = Ship(id=str(next_ship), name=ship_name)
    data["Ship"][new_ship.id] = new_ship
    data["Faction"][faction_id].ships.append(new_ship.id)
    return new_ship


def get_ship(_id):
    return data["Ship"][_id]


def get_faction(_id):
    return data["Faction"][_id]


def get_rebels():
    return get_faction("1")


def get_empire():
    return get_faction("2")
