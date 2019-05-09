class PaginatedResult(object):
    """
    An instance of this class is returned from paginated operations
    """

    def __init__(self, total_items, page_size, current_page):
        self.total_items = total_items
        self.page_size = page_size
        self.current_page = current_page
