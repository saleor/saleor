from ...page.models import Page, PageType
from ..core.dataloaders import DataLoader


class PageByIdLoader(DataLoader):
    context_key = "page_by_id"

    def batch_load(self, keys):
        pages = Page.objects.visible_to_user(self.user).in_bulk(keys)
        return [pages.get(page_id) for page_id in keys]


class PageTypeByIdLoader(DataLoader):
    context_key = "page_type_by_id"

    def batch_load(self, keys):
        page_types = PageType.objects.in_bulk(keys)
        return [page_types.get(page_type_id) for page_type_id in keys]
