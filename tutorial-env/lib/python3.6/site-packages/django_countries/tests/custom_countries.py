from django_countries import Countries


class FantasyCountries(Countries):
    only = ["NZ", ("NV", "Neverland")]
