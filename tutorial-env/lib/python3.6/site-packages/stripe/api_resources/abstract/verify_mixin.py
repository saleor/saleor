from __future__ import absolute_import, division, print_function

from stripe import util


class VerifyMixin(object):
    def verify(self, idempotency_key=None, **params):
        url = self.instance_url() + "/verify"
        headers = util.populate_headers(idempotency_key)
        self.refresh_from(self.request("post", url, params, headers))
        return self
