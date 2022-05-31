import graphene
from custom import error_codes as custom_error_codes
CustomErrorCode = graphene.Enum.from_enum(custom_error_codes.CustomErrorCode)
