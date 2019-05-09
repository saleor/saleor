class Connection(object):

    def __init__(self, edges, page_info):
        self.edges = edges
        self.page_info = page_info

    def to_dict(self):
        return {
            'edges': [e.to_dict() for e in self.edges],
            'pageInfo': self.page_info.to_dict(),
        }


class PageInfo(object):

    def __init__(self, start_cursor="", end_cursor="",
                 has_previous_page=False, has_next_page=False):
        self.startCursor = start_cursor
        self.endCursor = end_cursor
        self.hasPreviousPage = has_previous_page
        self.hasNextPage = has_next_page

    def to_dict(self):
        return {
            'startCursor': self.startCursor,
            'endCursor': self.endCursor,
            'hasPreviousPage': self.hasPreviousPage,
            'hasNextPage': self.hasNextPage,
        }


class Edge(object):

    def __init__(self, node, cursor):
        self.node = node
        self.cursor = cursor

    def to_dict(self):
        return {
            'node': self.node,
            'cursor': self.cursor,
        }
