from datetime import timedelta

import graphene
import pytest
from django.utils import timezone

from ....tests.utils import get_graphql_content
from ..mutations.test_promotion_update import PROMOTION_UPDATE_MUTATION


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_promotion_update(
    staff_api_client,
    description_json,
    permission_group_manage_discounts,
    catalogue_promotion,
    count_queries,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_discounts)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    variables = {
        "id": graphene.Node.to_global_id("Promotion", catalogue_promotion.id),
        "input": {
            "name": "Promotion",
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        },
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            PROMOTION_UPDATE_MUTATION,
            variables,
        )
    )

    # then
    data = content["data"]["promotionUpdate"]
    assert data["promotion"]
