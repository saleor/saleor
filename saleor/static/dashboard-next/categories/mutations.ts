import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { categoryDetailsFragment } from "./queries";
import {
  CategoryBulkDelete,
  CategoryBulkDeleteVariables
} from "./types/CategoryBulkDelete";
import {
  CategoryCreate,
  CategoryCreateVariables
} from "./types/CategoryCreate";
import {
  CategoryDelete,
  CategoryDeleteVariables
} from "./types/CategoryDelete";
import {
  CategoryUpdate,
  CategoryUpdateVariables
} from "./types/CategoryUpdate";

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
  CategoryDelete,
  CategoryDeleteVariables
>(categoryDeleteMutation);

export const categoryCreateMutation = gql`
  ${categoryDetailsFragment}
  mutation CategoryCreate($parent: ID, $input: CategoryInput!) {
    categoryCreate(parent: $parent, input: $input) {
      errors {
        field
        message
      }
      category {
        ...CategoryDetailsFragment
      }
    }
  }
`;
export const TypedCategoryCreateMutation = TypedMutation<
  CategoryCreate,
  CategoryCreateVariables
>(categoryCreateMutation);

export const categoryUpdateMutation = gql`
  ${categoryDetailsFragment}
  mutation CategoryUpdate($id: ID!, $input: CategoryInput!) {
    categoryUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      category {
        ...CategoryDetailsFragment
      }
    }
  }
`;
export const TypedCategoryUpdateMutation = TypedMutation<
  CategoryUpdate,
  CategoryUpdateVariables
>(categoryUpdateMutation);

export const categoryBulkDeleteMutation = gql`
  mutation CategoryBulkDelete($ids: [ID]!) {
    categoryBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedCategoryBulkDeleteMutation = TypedMutation<
  CategoryBulkDelete,
  CategoryBulkDeleteVariables
>(categoryBulkDeleteMutation);
