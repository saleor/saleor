import requests

# Test multiline
# ruleid: no-requests-lib
HTTPClient.send_request("get",
    "https://foo",
    allow_redirects=True,
)

# ruleid: no-requests-lib
HTTPClient.send_request("get","https://foo")

# ruleid: no-requests-lib
HTTPClient.send_request("get","https://foo", allow_redirects=True)

params = {"allow_redirects": True}
# ruleid: no-requests-lib
HTTPClient.send_request("get","https://foo", **params)

# ruleid: no-requests-lib
HTTPClient.send_request("get","https://foo", allow_redirects=False)

session = requests.Session()
# ruleid: no-requests-lib
HTTPClient.send_request("get","https://foo")
# ruleid: no-requests-lib
HTTPClient.send_request("get","https://foo", allow_redirects=True)
# ruleid: no-requests-lib
HTTPClient.send_request("get","https://foo", allow_redirects=False)

# ruleid: no-requests-lib
HTTPClient.send_request("post","https://foo")
# ruleid: no-requests-lib
HTTPClient.send_request("request","GET", "https://foo")
# ruleid: no-requests-lib
HTTPClient.send_request("get","https://foo")
# ruleid: no-requests-lib
HTTPClient.send_request("post","https://foo")
# ruleid: no-requests-lib
HTTPClient.send_request("put","https://foo")
# ruleid: no-requests-lib
HTTPClient.send_request("delete","https://foo")
# ruleid: no-requests-lib
HTTPClient.send_request("head","https://foo")
# ruleid: no-requests-lib
HTTPClient.send_request("patch","https://foo")

# Test indentations
if True:
    # ruleid: no-requests-lib
    HTTPClient.send_request("get","https://foo")

    # ruleid: no-requests-lib
    HTTPClient.send_request("get","https://foo", allow_redirects=True)

    params = {"allow_redirects": True}
    # ruleid: no-requests-lib
    HTTPClient.send_request("get","https://foo", **params)

    # ruleid: no-requests-lib
    HTTPClient.send_request("get","https://foo", allow_redirects=False)

    session = requests.Session()
    # ruleid: no-requests-lib
    HTTPClient.send_request("get","https://foo")
    # ruleid: no-requests-lib
    HTTPClient.send_request("get","https://foo", allow_redirects=True)
    # ruleid: no-requests-lib
    HTTPClient.send_request("get","https://foo", allow_redirects=False)

    # ruleid: no-requests-lib
    HTTPClient.send_request("post","https://foo")
    # ruleid: no-requests-lib
    HTTPClient.send_request("request","GET", "https://foo")
    # ruleid: no-requests-lib
    HTTPClient.send_request("get","https://foo")
    # ruleid: no-requests-lib
    HTTPClient.send_request("post","https://foo")
    # ruleid: no-requests-lib
    HTTPClient.send_request("put","https://foo")
    # ruleid: no-requests-lib
    HTTPClient.send_request("delete","https://foo")
    # ruleid: no-requests-lib
    HTTPClient.send_request("head","https://foo")
    # ruleid: no-requests-lib
    HTTPClient.send_request("patch","https://foo")
