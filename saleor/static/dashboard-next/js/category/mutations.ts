import gql from "graphql-tag";
import * as React from "react";
import { Mutation, MutationProps } from "react-apollo";

import {
  CategoryCreateMutation,
  CategoryCreateMutationVariables,
  CategoryDeleteMutation,
  CategoryDeleteMutationVariables,
  CategoryUpdateMutation,
  CategoryUpdateMutationVariables
} from "../gql-types";

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

export const TypedCategoryDeleteMutation: React.ComponentType<
  MutationProps<CategoryDeleteMutation, CategoryDeleteMutationVariables>
> = Mutation;

export const categoryCreateMutation = gql`
  mutation CategoryCreate($name: String!, $description: String, $parentId: ID) {
    categoryCreate(
      name: $name
      description: $description
      parentId: $parentId
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

export const TypedCategoryCreateMutation: React.ComponentType<
  MutationProps<CategoryCreateMutation, CategoryCreateMutationVariables>
> = Mutation;

export const categoryUpdateMutation = gql`
  mutation CategoryUpdate($id: ID!, $name: String!, $description: String!) {
    categoryUpdate(id: $id, name: $name, description: $description) {
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

export const TypedCategoryUpdateMutation: React.ComponentType<
  MutationProps<CategoryUpdateMutation, CategoryUpdateMutationVariables>
> = Mutation;
