import gql from "graphql-tag";

import { TypedQuery } from "../../core/queries";
import { basicProductFragment } from "../Product/queries";
import { Collection, CollectionVariables } from "./types/Collection";

export const collectionProductsQuery = gql`
  ${basicProductFragment}
  query Collection(
    $id: ID!
    $attributes: [AttributeScalar]
    $after: String
    $pageSize: Int
    $sortBy: ProductOrder
    $priceLte: Float
    $priceGte: Float
  ) {
    collection(id: $id) {
      id
      slug
      name
      seoDescription
      seoTitle
      backgroundImage {
        url
      }
    }
    products(
      collections: [$id]
      after: $after
      attributes: $attributes
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
    attributes(inCollection: $id, first: 100) {
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

export const TypedCollectionProductsQuery = TypedQuery<
  Collection,
  CollectionVariables
>(collectionProductsQuery);
