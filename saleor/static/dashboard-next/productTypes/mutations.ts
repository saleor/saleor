import gql from "graphql-tag";
import { Mutation, MutationProps } from "react-apollo";

import {
  ProductTypeDeleteMutation,
  ProductTypeDeleteMutationVariables
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
