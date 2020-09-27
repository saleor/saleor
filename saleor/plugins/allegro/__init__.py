from enum import Enum


class ProductPublishState(str, Enum):
    MODERATED = "moderated"
    PUBLISHED = "published"
    SOLD = "sold"
