import graphene
import pytest
from django.core.exceptions import ValidationError

from ....page.models import Page, PageType
from ....payment.error_codes import TransactionRequestActionErrorCode
from ..utils import resolve_reason_reference_page


def test_resolve_reason_reference_page_valid(site_settings):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    page_global_id = graphene.Node.to_global_id("Page", page.pk)

    # when
    result = resolve_reason_reference_page(
        page_global_id,
        page_type.pk,
        TransactionRequestActionErrorCode,
    )

    # then
    assert result == page


def test_resolve_reason_reference_page_wrong_page_type(site_settings):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    wrong_page_type = PageType.objects.create(name="Blog Posts", slug="blog-posts")
    page = Page.objects.create(
        slug="blog-post",
        title="Blog Post",
        page_type=wrong_page_type,
        is_published=True,
    )
    page_global_id = graphene.Node.to_global_id("Page", page.pk)

    # when / then
    with pytest.raises(ValidationError) as exc_info:
        resolve_reason_reference_page(
            page_global_id,
            page_type.pk,
            TransactionRequestActionErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert "reason_reference" in error_dict
    assert (
        error_dict["reason_reference"][0].code
        == TransactionRequestActionErrorCode.INVALID.value
    )
    assert "Invalid reason reference" in str(error_dict["reason_reference"][0])


def test_resolve_reason_reference_page_invalid_global_id(site_settings):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    product_global_id = graphene.Node.to_global_id("Product", 1)

    # when / then
    with pytest.raises(ValidationError) as exc_info:
        resolve_reason_reference_page(
            product_global_id,
            page_type.pk,
            TransactionRequestActionErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert "reason_reference" in error_dict
    assert (
        error_dict["reason_reference"][0].code
        == TransactionRequestActionErrorCode.GRAPHQL_ERROR.value
    )
    assert "Invalid reason reference" in str(error_dict["reason_reference"][0])
