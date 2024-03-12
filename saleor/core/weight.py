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


def zero_weight():
    """Represent the zero weight value."""
    return Weight(kg=0)


def convert_weight(weight: Weight, unit: str) -> Weight:
    """Covert weight to given unit and round it to 3 digits after decimal point."""
    # Weight amount from the Weight instance can be retrieved in several units
    # via its properties. eg. Weight(lb=10).kg
    converted_weight = getattr(weight, unit)
    weight = Weight(**{unit: converted_weight})
    weight.value = round(weight.value, 3)
    return weight


def get_default_weight_unit():
    site = Site.objects.get_current()
    return site.settings.default_weight_unit


def convert_weight_to_default_weight_unit(weight: Weight) -> Weight:
    """Weight is kept in one unit, but should be returned in site default unit."""
    default_unit = get_default_weight_unit()
    if weight is not None:
        if weight.unit != default_unit:
            weight = convert_weight(weight, default_unit)
        else:
            weight.value = round(weight.value, 3)
    return weight
