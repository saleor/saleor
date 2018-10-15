import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
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
  mutation CategoryCreate($input: CategoryInput!) {
    categoryCreate(input: $input) {
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
        seoDescription
        seoTitle
      }
    }
  }
`;
export const TypedCategoryCreateMutation = TypedMutation<
  CategoryCreate,
  CategoryCreateVariables
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
  CategoryUpdate,
  CategoryUpdateVariables
>(categoryUpdateMutation);
