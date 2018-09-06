import django_filters
from django.http import QueryDict

from saleor.dashboard.templatetags.chips import (
    CHIPS_PATTERN, handle_default, handle_multiple_choice,
    handle_multiple_model_choice, handle_nullboolean, handle_range,
    handle_single_choice, handle_single_model_choice)
from saleor.dashboard.widgets import MoneyRangeWidget
from saleor.product.models import Category, Product


def querydict(data):
    qd = QueryDict(mutable=True)
    qd.update(data)
    return qd


class CharFieldFilterSet(django_filters.FilterSet):
    name = django_filters.CharFilter(label='Name')


class ChoiceFieldFilterSet(django_filters.FilterSet):
    is_featured = django_filters.ChoiceFilter(
        label='Is featured', choices=[(0, 'Featured'), (1, 'Not featured')])


class MultipleChoiceFieldFilterSet(django_filters.FilterSet):
    is_featured = django_filters.MultipleChoiceFilter(
        label='Is featured', choices=[(0, 'Featured'), (1, 'Not featured')])


class NullBooleanFieldFilterSet(django_filters.FilterSet):
    is_featured = django_filters.BooleanFilter(label='Is featured')


class ModelChoiceFieldFilterSet(django_filters.FilterSet):
    categories = django_filters.ModelChoiceFilter(
        label='Category', queryset=Category.objects.all())


class ModelMultipleChoiceFieldFilterSet(django_filters.FilterSet):
    categories = django_filters.ModelMultipleChoiceFilter(
        label='Category', queryset=Category.objects.all())


class RangeFieldFilterSet(django_filters.FilterSet):
    price = django_filters.RangeFilter(
        label='Price', field_name='price', widget=MoneyRangeWidget)


def test_char_field_chip():
    data = querydict({'name': 'Milionare Pirate'})
    filter_set = CharFieldFilterSet(data, queryset=Product.objects.all())
    field = filter_set.form['name']
    items = handle_default(field, data)
    assert len(items) == 1
    chip = items[0]
    assert chip['content'] == CHIPS_PATTERN % ('Name', 'Milionare Pirate')
    assert 'name=Milionare+Pirate' not in chip['link']


def test_single_choice_chip():
    data = querydict({'is_featured': 0})
    filter_set = ChoiceFieldFilterSet(data, queryset=Product.objects.all())
    field = filter_set.form['is_featured']
    items = handle_single_choice(field, data)
    assert len(items) == 1
    chip = items[0]
    assert chip['content'] == CHIPS_PATTERN % ('Is featured', 'Featured')
    assert 'is_featured=0' not in chip['link']


def test_multiple_choice_chip():
    data = QueryDict(mutable=True)
    data.update({'is_featured': 0})
    data.update({'is_featured': 1})
    filter_set = MultipleChoiceFieldFilterSet(
        data, queryset=Product.objects.all())
    field = filter_set.form['is_featured']
    items = handle_multiple_choice(field, data)

    assert len(items) == 2
    chip_1 = items[0]
    assert chip_1['content'] == CHIPS_PATTERN % ('Is featured', 'Featured')
    assert 'is_featured=0' not in chip_1['link']
    assert 'is_featured=1' in chip_1['link']

    chip_2 = items[1]
    assert chip_2['content'] == CHIPS_PATTERN % ('Is featured', 'Not featured')
    assert 'is_featured=0' in chip_2['link']
    assert 'is_featured=1' not in chip_2['link']


def test_nullboolean_field_chip():
    data = querydict({'is_featured': 1})
    filter_set = ChoiceFieldFilterSet(data, queryset=Product.objects.all())
    field = filter_set.form['is_featured']
    items = handle_nullboolean(field, data)
    assert len(items) == 1
    chip = items[0]
    assert chip['content'] == CHIPS_PATTERN % ('Is featured', 'yes')
    assert 'is_featured=1' not in chip['link']


def test_model_choice_field_chip(category):
    obj = Category.objects.first()
    data = querydict({'categories': obj.pk})
    filter_set = ModelChoiceFieldFilterSet(
        data, queryset=Product.objects.all())
    field = filter_set.form['categories']
    items = handle_single_model_choice(field, data)
    assert len(items) == 1
    chip = items[0]
    assert chip['content'] == CHIPS_PATTERN % ('Category', str(obj))
    assert 'categories=%s' % obj.pk not in chip['link']


def test_model_multiple_choice_field_chip():
    obj_1 = Category.objects.get_or_create(name='test-1', slug='test-1')[0]
    obj_2 = Category.objects.get_or_create(name='test-2', slug='test-2')[0]

    data = QueryDict(mutable=True)
    data.update({'categories': obj_1.pk})
    data.update({'categories': obj_2.pk})

    filter_set = ModelMultipleChoiceFieldFilterSet(
        data, queryset=Product.objects.all())
    field = filter_set.form['categories']
    items = handle_multiple_model_choice(field, data)
    assert len(items) == 2

    chip_1 = items[0]
    assert chip_1['content'] == CHIPS_PATTERN % ('Category', str(obj_1))
    assert 'categories=%s' % obj_1.pk not in chip_1['link']
    assert 'categories=%s' % obj_2.pk in chip_1['link']

    chip_2 = items[1]
    assert chip_2['content'] == CHIPS_PATTERN % ('Category', str(obj_2))
    assert 'categories=%s' % obj_2.pk not in chip_2['link']
    assert 'categories=%s' % obj_1.pk in chip_2['link']


def test_range_field_chip():
    data = querydict({'price_min': 1, 'price_max': 50})
    filter_set = RangeFieldFilterSet(data, queryset=Product.objects.all())
    field = filter_set.form['price']
    items = handle_range(field, data)

    assert len(items) == 2
    chip_1 = items[0]
    assert chip_1['content'] == CHIPS_PATTERN % ('Price', 'From %s' % 1)
    assert 'price_min=1' not in chip_1['link']
    assert 'price_max=50' in chip_1['link']

    chip_2 = items[1]
    assert chip_2['content'] == CHIPS_PATTERN % ('Price', 'To %s' % 50)
    assert 'price_min=1' in chip_2['link']
    assert 'price_max=50' not in chip_2['link']
