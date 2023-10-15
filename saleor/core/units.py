class DistanceUnits:
    MM = "mm"
    CM = "cm"
    DM = "dm"
    M = "m"
    KM = "km"
    FT = "ft"
    YD = "yd"
    INCH = "inch"

    CHOICES = [
        (MM, "Millimeter"),
        (CM, "Centimeter"),
        (DM, "Decimeter"),
        (M, "Meter"),
        (KM, "Kilometers"),
        (FT, "Feet"),
        (YD, "Yard"),
        (INCH, "Inch"),
    ]


class AreaUnits:
    SQ_MM = "sq_mm"
    SQ_CM = "sq_cm"
    SQ_DM = "sq_dm"
    SQ_M = "sq_m"
    SQ_KM = "sq_km"
    SQ_FT = "sq_ft"
    SQ_YD = "sq_yd"
    SQ_INCH = "sq_inch"

    CHOICES = [
        (SQ_MM, "Square millimeter"),
        (SQ_CM, "Square centimeters"),
        (SQ_DM, "Square decimeter"),
        (SQ_M, "Square meters"),
        (SQ_KM, "Square kilometers"),
        (SQ_FT, "Square feet"),
        (SQ_YD, "Square yards"),
        (SQ_INCH, "Square inches"),
    ]


class VolumeUnits:
    CUBIC_MILLIMETER = "cubic_millimeter"
    CUBIC_CENTIMETER = "cubic_centimeter"
    CUBIC_DECIMETER = "cubic_decimeter"
    CUBIC_METER = "cubic_meter"
    LITER = "liter"
    CUBIC_FOOT = "cubic_foot"
    CUBIC_INCH = "cubic_inch"
    CUBIC_YARD = "cubic_yard"
    QT = "qt"
    PINT = "pint"
    FL_OZ = "fl_oz"
    ACRE_IN = "acre_in"
    ACRE_FT = "acre_ft"

    CHOICES = [
        (CUBIC_MILLIMETER, "Cubic millimeter"),
        (CUBIC_CENTIMETER, "Cubic centimeter"),
        (CUBIC_DECIMETER, "Cubic decimeter"),
        (CUBIC_METER, "Cubic meter"),
        (LITER, "Liter"),
        (CUBIC_FOOT, "Cubic foot"),
        (CUBIC_INCH, "Cubic inch"),
        (CUBIC_YARD, "Cubic yard"),
        (QT, "Quart"),
        (PINT, "Pint"),
        (FL_OZ, "Fluid ounce"),
        (ACRE_IN, "Acre inch"),
        (ACRE_FT, "Acre feet"),
    ]


class WeightUnits:
    G = "g"
    LB = "lb"
    OZ = "oz"
    KG = "kg"
    TONNE = "tonne"

    CHOICES = [
        (G, "Gram"),
        (LB, "Pound"),
        (OZ, "Ounce"),
        (KG, "kg"),
        (TONNE, "Tonne"),
    ]


def prepare_all_units_dict():
    measurement_dict = {
        unit.upper(): unit
        for unit_choices in [
            DistanceUnits.CHOICES,
            AreaUnits.CHOICES,
            VolumeUnits.CHOICES,
            WeightUnits.CHOICES,
        ]
        for unit, _ in unit_choices
    }
    return dict(measurement_dict, CHOICES=[(v, v) for v in measurement_dict.values()])


MeasurementUnits = type("MeasurementUnits", (object,), prepare_all_units_dict())
