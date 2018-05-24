import gql from "graphql-tag";
import { Mutation, MutationProps } from "react-apollo";

import {
  ProductImageCreateMutation,
  ProductImageCreateMutationVariables
} from "../gql-types";

export const TypedProductImageCreateMutation = Mutation as React.ComponentType<
  MutationProps<ProductImageCreateMutation, ProductImageCreateMutationVariables>
>;
export const productImageCreateMutation = gql`
  mutation ProductImageCreate($id: ID!, $file: Upload!) {
    productImageCreate(productId: $id, file: $file) {
      productImage {
        id
        image
        url
        order
      }
    }
  }
`;
