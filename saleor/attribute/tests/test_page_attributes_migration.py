from unittest.mock import patch

import pytest

from saleor.attribute.migrations.tasks.saleor3_16 import (
    assign_pages_to_attribute_values_task,
)
from saleor.attribute.models import AssignedPageAttributeValue


@pytest.mark.django_db
def test_update_page_assignment(second_page):
    page1, page2 = second_page
    apa_values_init = AssignedPageAttributeValue.objects.filter(
        assignment__page_id__in=[page1.id, page2.id]
    )
    # check that initially page field is populated in a default manner
    assert len(apa_values_init) == 12
    for assigned_page in apa_values_init:
        assert assigned_page.assignment.page.id == assigned_page.page.id

    # create state before migration
    AssignedPageAttributeValue.objects.filter(
        assignment__page_id__in=[page1.id, page2.id]
    ).update(page=None)

    apa_values_before_migration = AssignedPageAttributeValue.objects.filter(
        assignment__page_id__in=[page1.id, page2.id]
    )
    assert len(apa_values_before_migration) == 12
    for assigned_page in apa_values_before_migration:
        assert assigned_page.page is None

    with patch("saleor.attribute.migrations.tasks.saleor3_16.BATCH_SIZE", 5):
        assign_pages_to_attribute_values_task()

    apa_values_post_migration = AssignedPageAttributeValue.objects.filter(
        assignment__page_id__in=[page1.id, page2.id]
    )
    assert len(apa_values_post_migration) == 12
    for assigned_page in apa_values_post_migration:
        assert assigned_page.assignment.page.id == assigned_page.page.id
