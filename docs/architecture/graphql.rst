GraphQL API (Beta)
====================

.. note::

    The GraphQL API is in the early version and is subject to change.


Saleor supports GraphQL API. It allows to create apps that can handle fulfillment, orders, pages, product and shipping management.

GraphQL allows for more efficient data retrieval - it is easier to fetch all desired resources without redundant ones.

Learn more at `official website <https://graphql.org>`_.

Endpoint
--------
You can test API under ``/graphql`` endpoint - in default Saleor configuration URL would be ``http://localhost:8000/graphql/``. You can perform queries normally, however you need to log in to an account with proper permissions to run mutations and query for restricted data.


Query
-----
Saleor GraphQL uses `Relay connection standard <facebook.github.io/relay/graphql/connections.htm>`_, which is very handy in case of pagination.

Quering for data in GraphQL can be vary easy with tool GraphiQL, which can be used in the browser.

For example this query:

.. code-block:: html

    query happyThreeProducts {
      products(first: 3){
        edges {
          node {
            name
            price {
              amount
            }
          }
        }
      }
    }

results in the following result:

.. code-block:: html

    {
      "data": {
        "products": {
          "edges": [
            {
              "node": {
                "name": "Ford Inc",
                "price": {
                  "amount": 64.98
                }
              }
            },
            {
              "node": {
                "name": "Rodriguez Ltd",
                "price": {
                  "amount": 18.4
                }
              }
            },
            {
              "node": {
                "name": "Smith Inc",
                "price": {
                  "amount": 48.66
                }
              }
            }
          ]
        }
      }
    }

Authorization
----------------------------
Saleor GraphQL API uses `JWT <https://jwt.io/>`_ - to authorize you need to create and add token to the ``Authorization`` header. You can do it with the following mutation:

.. code-block:: html

    mutation tokenCreate($username: String!, $password: String!) {
      tokenAuth(username: $username, password: $password) {
        token
      }
    }

Verification and refreshing the token is very simple:

.. code-block:: html

    mutation tokenVerify($token: String!) {
      verifyToken(token: $token) {
        payload
      }
    }

.. code-block:: html

    mutation tokenRefresh($token: String!) {
      tokenRefresh(token: $token) {
        token
        payload
      }
    }
