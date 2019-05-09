from __future__ import absolute_import, division, print_function

from stripe import util
from stripe.stripe_object import StripeObject

from stripe.six.moves.urllib.parse import quote_plus


class ListObject(StripeObject):
    OBJECT_NAME = "list"

    def list(self, **params):
        return self.request("get", self["url"], params)

    def auto_paging_iter(self):
        page = self
        params = dict(self._retrieve_params)

        while True:
            item_id = None
            for item in page:
                item_id = item.get("id", None)
                yield item

            if not getattr(page, "has_more", False) or item_id is None:
                return

            params["starting_after"] = item_id
            page = self.list(**params)

    def create(self, idempotency_key=None, **params):
        headers = util.populate_headers(idempotency_key)
        return self.request("post", self["url"], params, headers)

    def retrieve(self, id, **params):
        base = self.get("url")
        id = util.utf8(id)
        extn = quote_plus(id)
        url = "%s/%s" % (base, extn)

        return self.request("get", url, params)

    def __iter__(self):
        return getattr(self, "data", []).__iter__()

    def __len__(self):
        return getattr(self, "data", []).__len__()
