from ...utils import get_graphql_content

TRANSACTION_EVENT_REPORT_MUTATION = """
    mutation TransactionEventReport(
        $id: ID
        $type: TransactionEventTypeEnum!
        $amount: PositiveDecimal!
        $pspReference: String!
        $time: DateTime
        $externalUrl: String
        $message: String
        $availableActions: [TransactionActionEnum!]!
    ) {
        transactionEventReport(
            id: $id
            type: $type
            amount: $amount
            pspReference: $pspReference
            time: $time
            externalUrl: $externalUrl
            message: $message
            availableActions: $availableActions
        ) {
            alreadyProcessed
            transaction {
                id
                actions
                pspReference
                events {
                    id
                }
                createdBy {
                    ... on User {
                        id
                    }
                    ... on App {
                        id
                    }
                }
            }
            transactionEvent {
                id
                createdAt
                pspReference
                message
                externalUrl
                amount {
                    currency
                    amount
                }
                type
                createdBy {
                ... on User {
                    id
                }
                ... on App {
                    id
                }
                }
            }
            errors {
                field
                code
            }
        }
    }
"""


def transaction_event_report(
    e2e_api_client,
    transaction_id,
    type,
    amount,
    psp_reference,
    external_url=None,
    event_time=None,
    message="",
    available_actions=None,
):
    if not available_actions:
        available_actions = []
    variables = {
        "id": transaction_id,
        "type": type,
        "amount": amount,
        "pspReference": psp_reference,
        "time": event_time,
        "externalUrl": external_url,
        "message": message,
        "availableActions": available_actions,
    }

    response = e2e_api_client.post_graphql(TRANSACTION_EVENT_REPORT_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["transactionEventReport"]["errors"] == []

    data = content["data"]["transactionEventReport"]
    assert data["transaction"]["id"] is not None
    assert data["transactionEvent"]["id"] is not None

    return data
