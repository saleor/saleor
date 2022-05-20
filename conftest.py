pytest_plugins = [
    "saleor.tests.fixtures",
    "saleor.plugins.tests.fixtures",
    "saleor.graphql.tests.fixtures",
    "saleor.graphql.channel.tests.fixtures",
    "saleor.graphql.account.tests.benchmark.fixtures",
    "saleor.graphql.order.tests.benchmark.fixtures",
    "saleor.graphql.giftcard.tests.benchmark.fixtures",
    "saleor.graphql.webhook.tests.benchmark.fixtures",
    "saleor.plugins.webhook.tests.subscription_webhooks.fixtures",
]
