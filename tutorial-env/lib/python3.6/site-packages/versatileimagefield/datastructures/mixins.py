from ..settings import cache


class DeleteAndClearCacheMixIn(object):

    def clear_cache(self):
        cache.delete(self.url)

    def delete(self):
        self.storage.delete(self.name)
        self.clear_cache()
