import json

from measurement.measures import Weight

from ...taxes import zero_money
from ..json_serializer import CustomJsonEncoder


def test_custom_json_encoder_dumps_money_objects():
    # given
    currency = "usd"
    input = {"money": zero_money(currency)}

    # when
    serialized_data = json.dumps(input, cls=CustomJsonEncoder)

    # then
    data = json.loads(serialized_data)
    assert data["money"]["_type"] == "Money"
    assert data["money"]["amount"] == "0"
    assert data["money"]["currency"] == currency


def test_custom_json_encoder_dumps_weight_objects():
    # given
    input = {"weight": Weight(kg=5)}

    # when
    serialized_data = json.dumps(input, cls=CustomJsonEncoder)

    # then
    data = json.loads(serialized_data)
    assert data["weight"] == "5.0:kg"
