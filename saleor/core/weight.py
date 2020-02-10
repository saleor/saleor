"""In Saleor we are using 'weight' instead of a 'mass'.

For those of us who are earth-bound, weight is what we usually experience.
Mass is a theoretical construct.
Unless we are dealing with inertia and momentum, we are encountering
the attractive force between ourselves and the earth,
the isolated effects of mass alone being a little more esoteric.

So even though mass is more fundamental, most people think
in terms of weight.

In the end, it does not really matter unless you travel between
different planets.
"""
from django.contrib.sites.models import Site
from measurement.measures import Weight


class WeightUnits:
    KILOGRAM = "kg"
    POUND = "lb"
    OUNCE = "oz"
    GRAM = "g"

    CHOICES = [
        (KILOGRAM, "kg"),
        (POUND, "lb"),
        (OUNCE, "oz"),
        (GRAM, "g"),
    ]


def zero_weight():
    """Represent the zero weight value."""
    return Weight(kg=0)


def convert_weight(weight, unit):
    # Weight amount from the Weight instance can be retrived in serveral units
    # via its properties. eg. Weight(lb=10).kg
    converted_weight = getattr(weight, unit)
    return Weight(**{unit: converted_weight})


def get_default_weight_unit():
    site = Site.objects.get_current()
    return site.settings.default_weight_unit
