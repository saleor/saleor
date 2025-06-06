def test_invalid_graphql_query_no_bad_request_logged(api_client, caplog):
    # given
    invalid_query = "{ invalidField }"

    # when
    response = api_client.post_graphql(invalid_query)

    # then
    assert response.status_code == 400
    assert len(caplog.records) == 0


def test_404_warning_logged(api_client, caplog):
    # given
    invalid_url = "/non-existent-endpoint/"

    # when
    response = api_client.get(invalid_url)

    # then
    assert response.status_code == 404
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert "Not Found" in caplog.records[0].message
