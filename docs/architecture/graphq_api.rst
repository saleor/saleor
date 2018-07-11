GraphQL API (Beta)
====================

.. note::

    The GraphQL API is in the early version and is subject to change.


Saleor supports GraphQL API. It allows to create apps that can handle fulfillment, orders, pages, product and shipping management.

You can test API under ``/graphql`` URL. You can perform queries normally, however you need to log in to an account with proper permissions to run mutations and query for restricted data.


Authorization
----------------------------
Saleor GraphQL API uses `JWT <https://jwt.io/>`_ - to authorize you need to create and add token to the ``Authorization`` header. You can do it with the following mutation:

.. code-block::

    mutation tokenCreate($username: String!, $password: String!) {
      tokenAuth(username: $username, password: $password) {
        token
      }
    }

Verification and refreshing the token is very simple:

.. code-block::

    mutation tokenVerify($token: String!) {
      verifyToken(token: $token) {
        payload
      }
    }

.. code-block::

    mutation tokenRefresh($token: String!) {
      tokenRefresh(token: $token) {
        token
        payload
      }
    }
