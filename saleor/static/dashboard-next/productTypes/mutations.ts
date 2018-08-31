import gql from "graphql-tag";

import {
  ProductTypeCreateMutation,
  ProductTypeCreateMutationVariables,
  ProductTypeDeleteMutation,
  ProductTypeDeleteMutationVariables,
  ProductTypeUpdateMutation,
  ProductTypeUpdateMutationVariables
} from "../gql-types";
import { TypedMutation } from "../mutations";

export const productTypeDeleteMutation = gql`
  mutation ProductTypeDelete($id: ID!) {
    productTypeDelete(id: $id) {
      errors {
        field
        message
      }
      productType {
        id
      }
    }
  }
`;
export const TypedProductTypeDeleteMutation = TypedMutation<
  ProductTypeDeleteMutation,
  ProductTypeDeleteMutationVariables
>(productTypeDeleteMutation);

export const productTypeUpdateMutation = gql`
  mutation ProductTypeUpdate($id: ID!, $input: ProductTypeInput!) {
    productTypeUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      productType {
        id
        name
        hasVariants
        taxRate
        productAttributes {
          edges {
            node {
              id
              slug
              name
            }
          }
        }
        variantAttributes {
          edges {
            node {
              id
              slug
              name
            }
          }
        }
        isShippingRequired
      }
    }
  }
`;
export const TypedProductTypeUpdateMutation = TypedMutation<
  ProductTypeUpdateMutation,
  ProductTypeUpdateMutationVariables
>(productTypeUpdateMutation);

export const productTypeCreateMutation = gql`
  mutation ProductTypeCreate($input: ProductTypeInput!) {
    productTypeCreate(input: $input) {
      errors {
        field
        message
      }
      productType {
        id
        name
        hasVariants
        productAttributes {
          edges {
            node {
              id
              slug
              name
            }
          }
        }
        variantAttributes {
          edges {
            node {
              id
              slug
              name
            }
          }
        }
        isShippingRequired
      }
    }
  }
`;
export const TypedProductTypeCreateMutation = TypedMutation<
  ProductTypeCreateMutation,
  ProductTypeCreateMutationVariables
>(productTypeCreateMutation);
