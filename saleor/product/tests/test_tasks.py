import logging
from datetime import timedelta
from unittest.mock import patch

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from freezegun import freeze_time

from ..models import ProductVariant
from ..tasks import (
    _get_deactivate_preorder_for_variant_task_name,
    deactivate_preorder_for_variant_task,
    delete_deactivate_preorder_for_variant_task,
    schedule_deactivate_preorder_for_variant_task,
    update_product_discounted_price_task,
    update_products_discounted_prices_of_discount_task,
    update_variants_names,
)


@patch("saleor.product.tasks.update_products_discounted_prices_of_discount")
def test_update_products_discounted_prices_of_discount_task(
    update_product_prices_mock, sale
):
    # when
    update_products_discounted_prices_of_discount_task(sale.id)

    # then
    update_product_prices_mock.assert_called_once_with(sale)


@patch("saleor.product.tasks.update_products_discounted_prices_of_discount")
def test_update_products_discounted_prices_of_discount_task_discount_does_not_exist(
    update_product_prices_mock, caplog
):
    # given
    caplog.set_level(logging.WARNING)
    discount_id = -1

    # when
    update_products_discounted_prices_of_discount_task(discount_id)

    # then
    update_product_prices_mock.assert_not_called()
    assert f"Cannot find discount with id: {discount_id}" in caplog.text


@patch("saleor.product.tasks.update_product_discounted_price")
def test_update_product_discounted_price_task(update_product_price_mock, product):
    # when
    update_product_discounted_price_task(product.id)

    # then
    update_product_price_mock.assert_called_once_with(product)


@patch("saleor.product.tasks.update_product_discounted_price")
def test_update_product_discounted_price_task_product_does_not_exist(
    update_product_price_mock, caplog
):
    # given
    caplog.set_level(logging.WARNING)
    product_id = -1

    # when
    update_product_discounted_price_task(product_id)

    # then
    update_product_price_mock.assert_not_called()
    assert f"Cannot find product with id: {product_id}" in caplog.text


@patch("saleor.product.tasks._update_variants_names")
def test_update_variants_names(
    update_variants_names_mock, product_type, size_attribute
):
    # when
    update_variants_names(product_type.id, [size_attribute.id])

    # then
    args, _ = update_variants_names_mock.call_args
    assert args[0] == product_type
    assert {arg.pk for arg in args[1]} == {size_attribute.pk}


@patch("saleor.product.tasks.update_products_discounted_prices_of_discount")
def test_update_variants_names_product_type_does_not_exist(
    update_variants_names_mock, caplog
):
    # given
    caplog.set_level(logging.WARNING)
    product_type_id = -1

    # when
    update_variants_names(product_type_id, [])

    # then
    update_variants_names_mock.assert_not_called()
    assert f"Cannot find product type with id: {product_type_id}" in caplog.text


@patch("saleor.product.tasks.deactivate_preorder_for_variant")
@patch("saleor.product.tasks.delete_deactivate_preorder_for_variant_task")
def test_deactivate_preorder_for_variant_task(
    mock_delete_deactivate_preorder_for_variant_task,
    mock_deactivate_preorder_for_variant,
    preorder_variant_end_date,
):
    with freeze_time(preorder_variant_end_date.preorder_end_date):
        deactivate_preorder_for_variant_task(preorder_variant_end_date.pk)

    mock_deactivate_preorder_for_variant.assert_called_once()
    mock_delete_deactivate_preorder_for_variant_task.assert_called_once()


@patch("saleor.product.tasks.deactivate_preorder_for_variant")
@patch("saleor.product.tasks.delete_deactivate_preorder_for_variant_task")
def test_deactivate_preorder_for_variant_task_no_product_variant(
    mock_delete_deactivate_preorder_for_variant_task,
    mock_deactivate_preorder_for_variant,
):
    """If product variant was removed, remove scheduled task."""
    pk = ProductVariant.objects.count() + 1
    assert not ProductVariant.objects.filter(pk=pk)

    deactivate_preorder_for_variant_task(pk)

    mock_deactivate_preorder_for_variant.assert_not_called()
    mock_delete_deactivate_preorder_for_variant_task.assert_called_once()


@patch("saleor.product.tasks.deactivate_preorder_for_variant")
@patch("saleor.product.tasks.delete_deactivate_preorder_for_variant_task")
def test_deactivate_preorder_for_variant_task_no_preorder_end_date(
    mock_delete_deactivate_preorder_for_variant_task,
    mock_deactivate_preorder_for_variant,
    preorder_variant_global_threshold,
):
    """If preorder was manually ended, remove scheduled task."""
    assert preorder_variant_global_threshold.preorder_end_date is None

    deactivate_preorder_for_variant_task(preorder_variant_global_threshold.pk)

    mock_deactivate_preorder_for_variant.assert_not_called()
    mock_delete_deactivate_preorder_for_variant_task.assert_called_once()


@patch("saleor.product.tasks.deactivate_preorder_for_variant")
@patch("saleor.product.tasks.delete_deactivate_preorder_for_variant_task")
def test_deactivate_preorder_for_variant_task_bad_preorder_end_date(
    mock_delete_deactivate_preorder_for_variant_task,
    mock_deactivate_preorder_for_variant,
    preorder_variant_end_date,
):
    """If task is called with a different date (e.g. different year),
    remove scheduled task."""
    preorder_end_date = preorder_variant_end_date.preorder_end_date
    with freeze_time(preorder_end_date.replace(year=preorder_end_date.year + 1)):
        deactivate_preorder_for_variant_task(preorder_variant_end_date.pk)

    mock_deactivate_preorder_for_variant.assert_not_called()
    mock_delete_deactivate_preorder_for_variant_task.assert_called_once()


def test_schedule_deactivate_preorder_for_variant_task(
    preorder_variant_end_date,
):
    schedules_before = CrontabSchedule.objects.count()
    tasks_before = PeriodicTask.objects.count()

    schedule_deactivate_preorder_for_variant_task(preorder_variant_end_date)

    assert CrontabSchedule.objects.count() == schedules_before + 1
    assert PeriodicTask.objects.count() == tasks_before + 1

    delete_deactivate_preorder_for_variant_task(preorder_variant_end_date.pk)

    assert CrontabSchedule.objects.count() == schedules_before
    assert PeriodicTask.objects.count() == tasks_before


@patch("saleor.product.tasks.update_schedule_deactivate_preorder_for_variant_task")
def test_schedule_deactivate_preorder_for_variant_task_no_update(
    mock_update_schedule_deactivate_preorder_for_variant_task,
    preorder_variant_end_date,
):
    schedules_before = CrontabSchedule.objects.count()
    tasks_before = PeriodicTask.objects.count()

    schedule_deactivate_preorder_for_variant_task(preorder_variant_end_date)

    assert CrontabSchedule.objects.count() == schedules_before + 1
    assert PeriodicTask.objects.count() == tasks_before + 1

    schedule_deactivate_preorder_for_variant_task(preorder_variant_end_date)
    mock_update_schedule_deactivate_preorder_for_variant_task.assert_not_called()


def test_schedule_deactivate_preorder_for_variant_task_update_existing_crontab(
    preorder_variant_end_date,
):
    schedules_before = CrontabSchedule.objects.count()
    tasks_before = PeriodicTask.objects.count()

    schedule_deactivate_preorder_for_variant_task(preorder_variant_end_date)

    new_preorder_end_date = preorder_variant_end_date.preorder_end_date + timedelta(
        days=1
    )
    preorder_variant_end_date.preorder_end_date = new_preorder_end_date

    schedule_deactivate_preorder_for_variant_task(preorder_variant_end_date)

    assert CrontabSchedule.objects.count() == schedules_before + 1
    assert PeriodicTask.objects.count() == tasks_before + 1

    periodic_task = (
        PeriodicTask.objects.filter(
            name=_get_deactivate_preorder_for_variant_task_name(
                preorder_variant_end_date.pk
            )
        )
        .select_related("crontab")
        .first()
    )
    assert periodic_task.crontab.day_of_month == str(new_preorder_end_date.date().day)


def test_schedule_deactivate_preorder_for_variant_task_update_new_crontab(
    preorder_variant_end_date,
):
    schedules_before = CrontabSchedule.objects.count()
    tasks_before = PeriodicTask.objects.count()

    schedule_deactivate_preorder_for_variant_task(preorder_variant_end_date)

    preorder_variant_end_date.pk = None
    preorder_variant_end_date.sku += "2"
    preorder_variant_end_date.save()

    schedule_deactivate_preorder_for_variant_task(preorder_variant_end_date)

    assert CrontabSchedule.objects.count() == schedules_before + 1
    assert PeriodicTask.objects.count() == tasks_before + 2

    new_preorder_end_date = preorder_variant_end_date.preorder_end_date + timedelta(
        days=1
    )
    preorder_variant_end_date.preorder_end_date = new_preorder_end_date

    schedule_deactivate_preorder_for_variant_task(preorder_variant_end_date)

    assert CrontabSchedule.objects.count() == schedules_before + 2
    assert PeriodicTask.objects.count() == tasks_before + 2

    periodic_task = (
        PeriodicTask.objects.filter(
            name=_get_deactivate_preorder_for_variant_task_name(
                preorder_variant_end_date.pk
            )
        )
        .select_related("crontab")
        .first()
    )
    assert periodic_task.crontab.day_of_month == str(new_preorder_end_date.date().day)
