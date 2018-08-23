import gql from "graphql-tag";
import { Mutation, MutationProps } from "react-apollo";

import {
  ProductTypeDeleteMutation,
  ProductTypeDeleteMutationVariables,
  ProductTypeUpdateMutation,
  ProductTypeUpdateMutationVariables
} from "../gql-types";

export const TypedProductTypeDeleteMutation = Mutation as React.ComponentType<
  MutationProps<ProductTypeDeleteMutation, ProductTypeDeleteMutationVariables>
>;
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

export const TypedProductTypeUpdateMutation = Mutation as React.ComponentType<
  MutationProps<ProductTypeUpdateMutation, ProductTypeUpdateMutationVariables>
>;
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
