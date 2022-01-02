from enum import Enum

import graphene

GENDER_CHOICES = (
    ("M", "Male"),
    ("F", "Female"),
    (
        "U",
        "Unsure",
    ),
)

GenderCodeEnum = graphene.Enum(
    "GenderCodeEnum",
    [(gender[0].replace("-", "_").upper(), gender[0]) for gender in GENDER_CHOICES],
)


class VendorErrorCode(Enum):
    GROUP_NOT_FOUND = "vendor_not_found"
    GROUP_ERROR = "vendor_error"
