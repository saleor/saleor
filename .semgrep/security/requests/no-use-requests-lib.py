import requests

# Test multiline
# ruleid: no-requests-lib
requests.get(
    "https://foo",
    allow_redirects=True,
)

# ruleid: no-requests-lib
requests.get("https://foo")

# ruleid: no-requests-lib
requests.get("https://foo", allow_redirects=True)

params = {"allow_redirects": True}
# ruleid: no-requests-lib
requests.get("https://foo", **params)

# ruleid: no-requests-lib
requests.get("https://foo", allow_redirects=False)

session = requests.Session()
# ruleid: no-requests-lib
session.get("https://foo")
# ruleid: no-requests-lib
session.get("https://foo", allow_redirects=True)
# ruleid: no-requests-lib
session.get("https://foo", allow_redirects=False)

# ruleid: no-requests-lib
requests.post("https://foo")
# ruleid: no-requests-lib
requests.request("GET", "https://foo")
# ruleid: no-requests-lib
requests.get("https://foo")
# ruleid: no-requests-lib
requests.post("https://foo")
# ruleid: no-requests-lib
requests.put("https://foo")
# ruleid: no-requests-lib
requests.delete("https://foo")
# ruleid: no-requests-lib
requests.head("https://foo")
# ruleid: no-requests-lib
requests.patch("https://foo")

# Test indentations
if True:
    # ruleid: no-requests-lib
    requests.get("https://foo")

    # ruleid: no-requests-lib
    requests.get("https://foo", allow_redirects=True)

    params = {"allow_redirects": True}
    # ruleid: no-requests-lib
    requests.get("https://foo", **params)

    # ruleid: no-requests-lib
    requests.get("https://foo", allow_redirects=False)

    session = requests.Session()
    # ruleid: no-requests-lib
    session.get("https://foo")
    # ruleid: no-requests-lib
    session.get("https://foo", allow_redirects=True)
    # ruleid: no-requests-lib
    session.get("https://foo", allow_redirects=False)

    # ruleid: no-requests-lib
    requests.post("https://foo")
    # ruleid: no-requests-lib
    requests.request("GET", "https://foo")
    # ruleid: no-requests-lib
    requests.get("https://foo")
    # ruleid: no-requests-lib
    requests.post("https://foo")
    # ruleid: no-requests-lib
    requests.put("https://foo")
    # ruleid: no-requests-lib
    requests.delete("https://foo")
    # ruleid: no-requests-lib
    requests.head("https://foo")
    # ruleid: no-requests-lib
    requests.patch("https://foo")
