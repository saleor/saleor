import pytest

from ..promotions.utils import create_promotion
from ..utils import assign_permissions


@pytest.mark.e2e
def test_checkout_products_on_fixed_promotion(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    # Before
    permissions = [permission_manage_discounts]
    assign_permissions(e2e_staff_api_client, permissions)

    promotion_name = "Promotion Fixed"
    create_promotion(e2e_staff_api_client, promotion_name)
