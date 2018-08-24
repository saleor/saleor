import gql from "graphql-tag";

import {
  CategoryCreateMutation,
  CategoryCreateMutationVariables,
  CategoryDeleteMutation,
  CategoryDeleteMutationVariables,
  CategoryUpdateMutation,
  CategoryUpdateMutationVariables
} from "../gql-types";
import { TypedMutation } from "../mutations";

export const categoryDeleteMutation = gql`
  mutation CategoryDelete($id: ID!) {
    categoryDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedCategoryDeleteMutation = TypedMutation<
  CategoryDeleteMutation,
  CategoryDeleteMutationVariables
>(categoryDeleteMutation);

export const categoryCreateMutation = gql`
  mutation CategoryCreate($name: String, $description: String, $parent: ID) {
    categoryCreate(
      input: { name: $name, description: $description, parent: $parent }
    ) {
      errors {
        field
        message
      }
      category {
        id
        name
        description
        parent {
          id
        }
      }
    }
  }
`;
export const TypedCategoryCreateMutation = TypedMutation<
  CategoryCreateMutation,
  CategoryCreateMutationVariables
>(categoryCreateMutation);

export const categoryUpdateMutation = gql`
  mutation CategoryUpdate($id: ID!, $name: String, $description: String) {
    categoryUpdate(id: $id, input: { name: $name, description: $description }) {
      errors {
        field
        message
      }
      category {
        id
        name
        description
        parent {
          id
        }
      }
    }
  }
`;
export const TypedCategoryUpdateMutation = TypedMutation<
  CategoryUpdateMutation,
  CategoryUpdateMutationVariables
>(categoryUpdateMutation);
