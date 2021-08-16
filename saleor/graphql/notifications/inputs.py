import graphene


class ExternalNotificationTriggerInput(graphene.InputObjectType):
    ids = graphene.List(graphene.ID, required=True, description="List of customer ids.")
    extra_payloads = graphene.JSONString(
        required=True, description="Additionaly payload."
    )
    external_event_type = graphene.String(
        required=True, description="External event type description."
    )
