from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from ..metadata.utils import update_metadata
from ..promotions.utils import create_promotion, promotions_query
from ..sales.utils import create_sale
from ..utils import assign_permissions

# Should be able to query promotions with a different parameters CORE_2118


# Step 1 - Promotions with the parameter: first: 10
@pytest.mark.e2e
def test_step_1_query_promotions_first_10_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )

    promotion_type = "CATALOGUE"
    for i in range(11):
        promotion_name = f"Promotion first {i + 1}"
        create_promotion(e2e_staff_api_client, promotion_name, promotion_type)

    promotions_list = promotions_query(e2e_staff_api_client, first=10)

    assert len(promotions_list) == 10


# Step 2 - Returns 10 promotions with CREATED_AT in descending order
@pytest.mark.e2e
def test_step_2_query_promotions_first_10_created_at_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )

    promotion_type = "CATALOGUE"
    promotion_dnm = create_promotion(
        e2e_staff_api_client, "Promotion does not match", promotion_type
    )

    for i in range(10):
        promotion_name = f"Promotion {i + 1}"
        create_promotion(e2e_staff_api_client, promotion_name, promotion_type)

    promotions_list = promotions_query(
        e2e_staff_api_client,
        first=10,
        sort_by={"field": "CREATED_AT", "direction": "DESC"},
    )

    assert len(promotions_list) == 10

    for i in range(1, len(promotions_list)):
        prev_promotion = promotions_list[i - 1]["node"]
        current_promotion = promotions_list[i]["node"]

        prev_promo_created_at = datetime.fromisoformat(prev_promotion["createdAt"])
        current_promo_created_at = datetime.fromisoformat(
            current_promotion["createdAt"]
        )
        assert current_promotion["id"] != promotion_dnm["id"]
        assert prev_promo_created_at > current_promo_created_at


# Step 3 - Returns 10 promotions with startDate before a date in descending order
@pytest.mark.e2e
def test_step_3_query_promotions_first_10_start_date_before_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )

    promotion_type = "CATALOGUE"
    promotion_dnm = create_promotion(
        e2e_staff_api_client, "Promotion does not match", promotion_type
    )

    base_date = datetime(2023, 1, 1, 14, 1, 34, 61119)

    with freeze_time(base_date):
        for i in range(10):
            promotion_name = f"Promotion start date before {i + 1}"
            start_date = (base_date - timedelta(days=i + 1)).isoformat() + "+00:00"
            promotion = create_promotion(
                e2e_staff_api_client,
                promotion_name,
                promotion_type,
                start_date=start_date,
            )
            assert promotion["startDate"] == start_date

    promotions_list = promotions_query(
        e2e_staff_api_client,
        first=11,
        sort_by={
            "field": "START_DATE",
            "direction": "DESC",
        },
        where={"startDate": {"range": {"lte": "2023-07-28T14:01:34.061119+00:00"}}},
    )

    assert len(promotions_list) == 10

    for i in range(1, len(promotions_list)):
        prev_promotion = promotions_list[i - 1]["node"]
        current_promotion = promotions_list[i]["node"]

        prev_promo_start_date = datetime.fromisoformat(prev_promotion["startDate"])
        current_promo_start_date = datetime.fromisoformat(
            current_promotion["startDate"]
        )
        assert prev_promo_start_date >= current_promo_start_date
        assert current_promotion["id"] != promotion_dnm["id"]


# Step 4 - Returns 10 old sale promotions in descending order
@pytest.mark.e2e
def test_step_4_old_sales_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )

    for i in range(10):
        sale_name = f"Old sale {i + 1}"
        create_sale(
            e2e_staff_api_client,
            sale_name,
            sale_type="FIXED",
        )

    promotion_dnm = create_promotion(
        e2e_staff_api_client, "Promotion does not match", "CATALOGUE"
    )

    old_sale_promotions = promotions_query(
        e2e_staff_api_client,
        first=11,
        where={"isOldSale": True},
    )
    assert len(old_sale_promotions) == 10

    for i in range(10):
        assert old_sale_promotions[i]["node"]["id"] != promotion_dnm["id"]


# Step 5 - Returns 10 promotions with metadata
@pytest.mark.e2e
def test_step_5_promotions_with_metadata_CORE_211(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )

    metadata = []
    promotion_type = "CATALOGUE"

    for i in range(10):
        promotion_name = f"Promotion with metadata {i + 1}"
        promotion_with_metadata = create_promotion(
            e2e_staff_api_client, promotion_name, promotion_type
        )
        promotion_id = promotion_with_metadata["id"]
        assert promotion_id is not None

        metadata = [{"key": "pub", "value": "test"}]
        update_metadata(
            e2e_staff_api_client,
            promotion_id,
            metadata,
        )

    promotion_dnm = create_promotion(
        e2e_staff_api_client, "Promotion does not match", promotion_type
    )

    promotions_list = promotions_query(
        e2e_staff_api_client, first=11, where={"metadata": [{"key": "pub"}]}
    )
    assert len(promotions_list) == 10

    for i in range(10):
        assert promotions_list[i]["node"]["metadata"] == metadata
        assert promotions_list[i]["node"]["id"] != promotion_dnm["id"]


# Step 6 - Returns promotions with one of the names
@pytest.mark.e2e
def test_step_6_promotions_with_one_of_names_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )

    promotion_type = "CATALOGUE"
    for i in range(3):
        promotion_name = f"Promotion {i + 1}"
        create_promotion(e2e_staff_api_client, promotion_name, promotion_type)
    for i in range(3):
        promotion_name = f"Test {i + 1}"
        create_promotion(
            e2e_staff_api_client,
            promotion_name,
            promotion_type,
        )
    promotions_list = promotions_query(
        e2e_staff_api_client,
        sort_by={"field": "NAME", "direction": "ASC"},
        where={"name": {"oneOf": ["Promotion 2", "Test 3"]}},
    )
    assert len(promotions_list) == 2
    assert promotions_list[0]["node"]["name"] == "Promotion 2"
    assert promotions_list[1]["node"]["name"] == "Test 3"


# Step 7 - Returns promotions with name equal to
@pytest.mark.e2e
def test_step_7_promotions_with_name_eq_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )
    promotion_type = "CATALOGUE"
    for i in range(3):
        promotion_name = f"Promotion {i + 1}"
        create_promotion(
            e2e_staff_api_client,
            promotion_name,
            promotion_type,
        )
    promotions_list = promotions_query(
        e2e_staff_api_client,
        first=4,
        where={"name": {"eq": "Promotion 3"}},
    )
    assert len(promotions_list) == 1
    assert promotions_list[0]["node"]["name"] == "Promotion 3"


# Step 8 - Returns old sale promotions with a name
@pytest.mark.e2e
def test_step_8_query_old_sales_with_name_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )

    for i in range(3):
        sale_name = f"Old sale {i + 1}"
        create_sale(
            e2e_staff_api_client,
            sale_name,
            sale_type="FIXED",
        )

    promotion_dnm = create_promotion(e2e_staff_api_client, "Old sale 2", "CATALOGUE")

    promotions = promotions_query(
        e2e_staff_api_client,
        first=4,
        where={"AND": [{"name": {"eq": "Old sale 2"}}, {"isOldSale": True}]},
    )
    assert len(promotions) == 1
    assert promotions[0]["node"]["name"] == "Old sale 2"
    assert promotions[0]["node"]["id"] != promotion_dnm["id"]


# Step 9 - Returns 10 old sale promotions with one of the names
@pytest.mark.e2e
def test_step_9_query_old_sales_with_one_of_the_names_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )

    for i in range(3):
        sale_name = f"Old sale {i + 1}"
        create_sale(
            e2e_staff_api_client,
            sale_name,
            sale_type="FIXED",
        )
    for i in range(3):
        sale_name = f"Test {i + 1}"
        create_sale(
            e2e_staff_api_client,
            sale_name,
            sale_type="PERCENTAGE",
        )

    promotions_list = promotions_query(
        e2e_staff_api_client,
        first=7,
        sort_by={"field": "NAME", "direction": "ASC"},
        where={
            "AND": [{"name": {"oneOf": ["Old sale 2", "Test 3"]}}, {"isOldSale": True}]
        },
    )

    assert len(promotions_list) == 2
    assert promotions_list[0]["node"]["name"] == "Old sale 2"
    assert promotions_list[1]["node"]["name"] == "Test 3"


# Step 10 - Returns promotions with end date after a date
@pytest.mark.e2e
def test_step_10_promotions_with_end_date_after_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )
    base_date = datetime(2023, 1, 1, 14, 1, 34, 61119)
    now = base_date.isoformat()
    promotion_type = "CATALOGUE"

    with freeze_time(now):
        for i in range(10):
            promotion_name = f"Promotion end date after {i + 1}"
            end_date = (
                datetime.fromisoformat("2023-10-08T10:19:50.812975+00:00")
                + timedelta(days=i + 1)
            ).isoformat()
            promotion = create_promotion(
                e2e_staff_api_client,
                promotion_name,
                promotion_type,
                start_date="2023-10-04T00:00:00+02:00",
                end_date=end_date,
            )
            assert promotion["endDate"] == end_date

    promotion_dnm = create_promotion(
        e2e_staff_api_client,
        "Promotion does not match",
        promotion_type,
        end_date="2024-12-31T21:00:00.000000+00:00",
    )

    promotions_list = promotions_query(
        e2e_staff_api_client,
        first=11,
        sort_by={
            "field": "END_DATE",
            "direction": "DESC",
        },
        where={
            "endDate": {
                "range": {
                    "gte": "2023-07-28T14:01:34.061119+00:00",
                    "lte": "2023-11-08T10:19:50.812975+00:00",
                }
            }
        },
    )

    assert len(promotions_list) == 10

    for i in range(1, len(promotions_list)):
        prev_promotion = promotions_list[i - 1]["node"]
        current_promotion = promotions_list[i]["node"]
        prev_promo_end_date = datetime.fromisoformat(prev_promotion["endDate"])
        current_promo_end_date = datetime.fromisoformat(current_promotion["endDate"])
        assert prev_promo_end_date > current_promo_end_date
        assert current_promotion["id"] != promotion_dnm["id"]


# Step 11 - Returns promotions with no end date
@pytest.mark.e2e
def test_step_11_promotions_with_no_date_CORE_2118(
    e2e_staff_api_client,
    permission_manage_discounts,
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_discounts],
    )
    promotion_type = "CATALOGUE"
    for i in range(10):
        promotion_name = f"Promotion without end date {i + 1}"
        promotion = create_promotion(
            e2e_staff_api_client, promotion_name, promotion_type
        )
        assert promotion["endDate"] is None

    base_date = datetime(2023, 1, 1, 14, 1, 34, 61119)
    now = base_date.isoformat()

    with freeze_time(now):
        end_date = datetime.fromisoformat(
            "2023-10-08T10:19:50.812975+00:00"
        ).isoformat()
        promotion_dnm = create_promotion(
            e2e_staff_api_client,
            promotion_name="With end date",
            promotion_type=promotion_type,
            start_date="2023-10-04T00:00:00+02:00",
            end_date=end_date,
        )

    promotions_list = promotions_query(
        e2e_staff_api_client,
        first=11,
        sort_by={
            "field": "CREATED_AT",
            "direction": "DESC",
        },
        where={"endDate": {"eq": None}},
    )

    assert len(promotions_list) == 10

    for i in range(10):
        assert promotions_list[i]["node"]["endDate"] is None
        assert promotions_list[i]["node"]["id"] != promotion_dnm["id"]
