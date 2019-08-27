from unittest.mock import Mock

import pytest
from django.urls import reverse

from saleor.graphql.middleware import bot_middleware


@pytest.mark.parametrize("path, should_accept", [("api", True), ("home", False)])
def test_bot_middleware(bot, path, should_accept, rf):

    # Retrieve sample request object
    request = rf.get(reverse("api"))

    request.path = reverse(path)
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {bot.auth_token}"}

    middleware = bot_middleware(Mock())
    middleware(request)

    if should_accept:
        assert request.bot == bot
    else:
        assert not hasattr(request, "bot")
