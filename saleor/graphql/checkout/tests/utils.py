def assert_address_data(address, address_data, validation_skipped=False):
    if metadata := address_data.get("metadata"):
        assert address.metadata == {data["key"]: data["value"] for data in metadata}

    assert address is not None
    assert address.first_name == address_data["firstName"]
    assert address.last_name == address_data["lastName"]
    assert address.street_address_1 == address_data["streetAddress1"]
    assert address.street_address_2 == address_data["streetAddress2"]
    assert address.postal_code == address_data["postalCode"]
    assert address.country == address_data["country"]
    assert address.city == address_data["city"].upper()
    assert address.validation_skipped == validation_skipped
