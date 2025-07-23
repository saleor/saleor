QUERY_PAGES_WITH_WHERE = """
    query ($where: PageWhereInput) {
        pages(first: 5, where:$where) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
"""
