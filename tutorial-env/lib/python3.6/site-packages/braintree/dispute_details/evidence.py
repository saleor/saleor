from braintree.attribute_getter import AttributeGetter

class DisputeEvidence(AttributeGetter):
    def __init__(self, attributes):
        attributes["tag"] = attributes.get("category")
        AttributeGetter.__init__(self, attributes)
