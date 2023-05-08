from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=300)


class Gender:
    MALE = "M"
    FEMALE = "F"

    CHOICES = [(MALE, "Male"), (FEMALE, "Female")]
