from functools import partial

import graphene
from django.db.models.query import QuerySet
from django_measurement.models import MeasurementField
from django_prices.models import MoneyField, TaxedMoneyField
from graphene.relay import PageInfo
from graphene_django.converter import convert_django_field
from graphene_django.fields import DjangoConnectionField
from graphql_relay.connection.arrayconnection import connection_from_list_slice

from .types.common import Weight
from .types.money import Money, TaxedMoney


@convert_django_field.register(TaxedMoneyField)
def convert_field_taxed_money(field, registry=None):
    return graphene.Field(TaxedMoney)


@convert_django_field.register(MoneyField)
def convert_field_money(field, registry=None):
    return graphene.Field(Money)


@convert_django_field.register(MeasurementField)
def convert_field_measurements(field, registry=None):
    return graphene.Field(Weight)


class PrefetchingConnectionField(DjangoConnectionField):
    @classmethod
    def connection_resolver(
            cls, resolver, connection, default_manager, max_limit,
            enforce_first_or_last, root, info, **args):

        # Disable `enforce_first_or_last` if not querying for `edges`.
        values = [
            field.name.value
            for field in info.field_asts[0].selection_set.selections]
        if 'edges' not in values:
            enforce_first_or_last = False

        return super().connection_resolver(
            resolver, connection, default_manager, max_limit,
            enforce_first_or_last, root, info, **args)

    @classmethod
    def resolve_connection(cls, connection, default_manager, args, iterable):
        if iterable is None:
            iterable = default_manager

        if isinstance(iterable, QuerySet):
            _len = iterable.count()
        else:
            _len = len(iterable)

        connection = connection_from_list_slice(
            iterable,
            args,
            slice_start=0,
            list_length=_len,
            list_slice_length=_len,
            connection_type=connection,
            edge_type=connection.Edge,
            pageinfo_type=PageInfo,
        )
        connection.iterable = iterable
        connection.length = _len
        return connection


class FilterInputConnectionField(DjangoConnectionField):
    def __init__(self,  *args, **kwargs):
        self.filters_name = kwargs.pop('filters_name', 'filters')
        self.filters_obj = kwargs.get(self.filters_name)
        self.filterset_class = None
        if self.filters_obj:
            self.filterset_class = self.filters_obj.filterset_class
        super().__init__(*args, **kwargs)

    @classmethod
    def connection_resolver(
            cls, resolver, connection, default_manager, max_limit,
            enforce_first_or_last, filterset_class, filters_name, root, info,
            **args):

        # Disable `enforce_first_or_last` if not querying for `edges`.
        values = [
            field.name.value
            for field in info.field_asts[0].selection_set.selections]
        if 'edges' not in values:
            enforce_first_or_last = False

        filters_input = args.get(filters_name)
        qs = default_manager.get_queryset()
        if filters_input and filterset_class:
            qs = filterset_class(
                data=dict(filters_input),
                queryset=default_manager.get_queryset(),
                request=info.context).qs

        return super().connection_resolver(
            resolver,
            connection,
            qs,
            max_limit,
            enforce_first_or_last,
            root,
            info,
            **args
        )

    def get_resolver(self, parent_resolver):
        return partial(
            self.connection_resolver,
            parent_resolver,
            self.type,
            self.get_manager(),
            self.max_limit,
            self.enforce_first_or_last,
            self.filterset_class,
            self.filters_name
        )
