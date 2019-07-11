import gql from "graphql-tag";

import { TypedQuery } from "../../core/queries";
import {
  ProductDetails,
  ProductDetailsVariables
} from "./types/ProductDetails";
import { VariantList, VariantListVariables } from "./types/VariantList";

export const basicProductFragment = gql`
  fragment BasicProductFields on Product {
    id
    name
    thumbnail {
      url
      alt
    }
    thumbnail2x: thumbnail(size: 510) {
      url
    }
  }
`;

export const productVariantFragment = gql`
  fragment ProductVariantFields on ProductVariant {
    id
    sku
    name
    stockQuantity
    isAvailable
    price {
      currency
      amount
      localized
    }
    attributes {
      attribute {
        id
        name
      }
      value {
        id
        name
        value: name
      }
    }
  }
`;

export const productDetailsQuery = gql`
  ${basicProductFragment}
  ${productVariantFragment}
  query ProductDetails($id: ID!) {
    product(id: $id) {
      ...BasicProductFields
      descriptionJson
      category {
        id
        name
        products(first: 4) {
          edges {
            node {
              ...BasicProductFields
              category {
                id
                name
              }
              price {
                amount
                currency
                localized
              }
            }
          }
        }
      }
      price {
        amount
        currency
        localized
      }
      images {
        id
        url
      }
      variants {
        ...ProductVariantFields
      }
      seoDescription
      seoTitle
      availability {
        available
      }
    }
  }
`;

// FIXME: Check how to handle pagination of `productVariants` in the UI.
// We need allow the user view  all cart items regardless of pagination.
export const productVariatnsQuery = gql`
  ${basicProductFragment}
  ${productVariantFragment}
  query VariantList($ids: [ID!]) {
    productVariants(ids: $ids, first: 100) {
      edges {
        node {
          ...ProductVariantFields
          stockQuantity
          product {
            ...BasicProductFields
          }
        }
      }
    }
  }
`;

export const TypedProductDetailsQuery = TypedQuery<
  ProductDetails,
  ProductDetailsVariables
>(productDetailsQuery);

export const TypedProductVariantsQuery = TypedQuery<
  VariantList,
  VariantListVariables
>(productVariatnsQuery);
