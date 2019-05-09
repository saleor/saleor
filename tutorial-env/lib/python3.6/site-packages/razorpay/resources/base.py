class Resource(object):

    def __init__(self, client=None):
        self.client = client

    def all(self, data, **kwargs):
        return self.get_url(self.base_url, data, **kwargs)

    def fetch(self, id, data, **kwargs):
        url = "{}/{}".format(self.base_url, id)
        return self.get_url(url, data, **kwargs)

    def get_url(self, url, data, **kwargs):
        return self.client.get(url, data, **kwargs)

    def patch_url(self, url, data, **kwargs):
        return self.client.patch(url, data, **kwargs)

    def post_url(self, url, data, **kwargs):
        return self.client.post(url, data, **kwargs)

    def put_url(self, url, data, **kwargs):
        return self.client.put(url, data, **kwargs)

    def delete_url(self, url, data, **kwargs):
        return self.client.delete(url, data, **kwargs)

    def delete(self, id, data, **kwargs):
        url = "{}/{}/delete".format(self.base_url, id)
        return self.delete_url(url, data, **kwargs)
