import gql from "graphql-tag";
import { Query, QueryProps } from "react-apollo";

import {
  ProductDetailsQuery,
  ProductDetailsQueryVariables,
  ProductListQuery,
  ProductListQueryVariables
} from "../gql-types";

export const TypedProductListQuery = Query as React.ComponentType<
  QueryProps<ProductListQuery, ProductListQueryVariables>
  >;

export const productListQuery = gql`
  query ProductList($first: Int, $after: String, $last: Int, $before: String) {
    products(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          id
          name
          thumbnailUrl
          productType {
            id
            name
          }
        }
      }
      pageInfo {
        hasPreviousPage
        hasNextPage
        startCursor
        endCursor
      }
    }
  }
`;

export const TypedProductDetailsQuery = Query as React.ComponentType<
  QueryProps<ProductDetailsQuery, ProductDetailsQueryVariables>
  >;

export const productDetailsQuery = gql`
  fragment Money on Money {
    amount
    currency
    localized
  }
  query ProductDetails($id: ID!) {
    product(id: $id) {
      id
      name
      description
      seoTitle
      seoDescription
      category {
        id
        name
      }
      collections {
        edges {
          node {
            id
            name
          }
        }
      }
      price {
        ...Money
      }
      margin {
        start
        stop
      }
      purchaseCost {
        start {
          ...Money
        }
        stop {
          ...Money
        }
      }
      isPublished
      availableOn
      attributes {
        attribute {
          slug
          name
          values {
            name
            slug
          }
        }
        value {
          id
          name
        }
      }
      availability {
        available
        priceRange {
          start {
            net {
              ...Money
            }
          }
          stop {
            net {
              ...Money
            }
          }
        }
      }
      images {
        edges {
          node {
            id
            alt
            sortOrder
            url
          }
        }
      }
      variants {
        edges {
          node {
            id
            sku
            name
            priceOverride {
              ...Money
            }
            stockQuantity
            margin
          }
        }
      }
      productType {
        id
        name
      }
      url
    }
    collections {
      edges {
        node {
          id
          name
        }
      }
    }
    categories {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;
