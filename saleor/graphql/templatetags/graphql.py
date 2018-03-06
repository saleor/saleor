import graphene
from django.template import Library

register = Library()


@register.simple_tag
def pk_to_global_id(type, pk):
    return graphene.Node.to_global_id(type, pk)
