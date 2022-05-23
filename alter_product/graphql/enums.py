import graphene
from alter_product import error_codes as alter_product_errorCode

AlterProductErrorCode = graphene.Enum.from_enum(
    alter_product_errorCode.AlterProductErrorCode)
