import os


database_name = 'GeoLite2-City.mmdb'


def geolite2_database():
    return os.path.join(os.path.dirname(__file__), database_name)
