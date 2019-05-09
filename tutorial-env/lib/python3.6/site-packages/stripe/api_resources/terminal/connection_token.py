from __future__ import absolute_import, division, print_function

from stripe.api_resources.abstract import CreateableAPIResource


class ConnectionToken(CreateableAPIResource):
    OBJECT_NAME = "terminal.connection_token"
