from enum import Enum

import graphene

from ..types.common import Error


class ErrorCodeTest(Enum):
    INVALID = "invalid"


ErrorCodeTest = graphene.Enum.from_enum(ErrorCodeTest)


class ErrorTest(Error):
    code = ErrorCodeTest()
