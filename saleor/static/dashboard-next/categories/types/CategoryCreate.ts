/* tslint:disable */
// This file was automatically generated and should not be edited.

import { CategoryInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CategoryCreate
// ====================================================

export interface CategoryCreate_categoryCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CategoryCreate_categoryCreate_category_parent {
  __typename: "Category";
  id: string;
}

export interface CategoryCreate_categoryCreate_category {
  __typename: "Category";
  id: string;
  name: string;
  description: string;
  seoDescription: string | null;
  seoTitle: string | null;
  parent: CategoryCreate_categoryCreate_category_parent | null;
}

export interface CategoryCreate_categoryCreate {
  __typename: "CategoryCreate";
  errors: (CategoryCreate_categoryCreate_errors | null)[] | null;
  category: CategoryCreate_categoryCreate_category | null;
}

export interface CategoryCreate {
  categoryCreate: CategoryCreate_categoryCreate | null;
}

export interface CategoryCreateVariables {
  input: CategoryInput;
}
