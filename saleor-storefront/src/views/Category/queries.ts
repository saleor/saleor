import gql from "graphql-tag";

import { TypedQuery } from "../../core/queries";
import { basicProductFragment } from "../Product/queries";
import { Category, CategoryVariables } from "./types/Category";

export const categoryProductsQuery = gql`
  ${basicProductFragment}
  query Category(
    $id: ID!
    $attributes: [AttributeScalar]
    $after: String
    $pageSize: Int
    $sortBy: ProductOrder
    $priceLte: Float
    $priceGte: Float
  ) {
    products(
      after: $after
      attributes: $attributes
      categories: [$id]
      first: $pageSize
      sortBy: $sortBy
      priceLte: $priceLte
      priceGte: $priceGte
    ) {
      totalCount
      edges {
        node {
          ...BasicProductFields
          price {
            amount
            currency
            localized
          }
          category {
            id
            name
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
      }
    }
    category(id: $id) {
      seoDescription
      seoTitle
      id
      name
      backgroundImage {
        url
      }
      ancestors(last: 5) {
        edges {
          node {
            id
            name
          }
        }
      }
    }
    attributes(inCategory: $id, first: 100) {
      edges {
        node {
          id
          name
          slug
          values {
            id
            name
            slug
          }
        }
      }
    }
  }
`;

export const TypedCategoryProductsQuery = TypedQuery<
  Category,
  CategoryVariables
>(categoryProductsQuery);
