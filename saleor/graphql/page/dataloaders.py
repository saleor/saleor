from ...page.models import Page
from ..core.dataloaders import DataLoader


class PageByIdLoader(DataLoader):
    context_key = "page_by_id"

    def batch_load(self, keys):
        pages = Page.objects.visible_to_user(self.user).in_bulk(keys)
        return [pages.get(page_id) for page_id in keys]
