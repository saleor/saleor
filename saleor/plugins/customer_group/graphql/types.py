from graphene_django import DjangoObjectType

from saleor.plugins.customer_group.models import CustomerGroup


class CustomerGroupType(DjangoObjectType):
    class Meta:
        model = CustomerGroup
        fields = "__all__"
