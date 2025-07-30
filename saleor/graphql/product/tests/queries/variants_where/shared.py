PRODUCT_VARIANTS_WHERE_QUERY = """
    query($where: ProductVariantWhereInput!, $channel: String) {
      productVariants(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            id
            name
            sku
          }
        }
      }
    }
"""
