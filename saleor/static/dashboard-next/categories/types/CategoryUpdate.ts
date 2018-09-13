/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CategoryUpdate
// ====================================================

export interface CategoryUpdate_categoryUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CategoryUpdate_categoryUpdate_category_parent {
  __typename: "Category";
  id: string;
}

export interface CategoryUpdate_categoryUpdate_category {
  __typename: "Category";
  id: string;
  name: string;
  description: string;
  parent: CategoryUpdate_categoryUpdate_category_parent | null;
}

export interface CategoryUpdate_categoryUpdate {
  __typename: "CategoryUpdate";
  errors: (CategoryUpdate_categoryUpdate_errors | null)[] | null;
  category: CategoryUpdate_categoryUpdate_category | null;
}

export interface CategoryUpdate {
  categoryUpdate: CategoryUpdate_categoryUpdate | null;
}

export interface CategoryUpdateVariables {
  id: string;
  name?: string | null;
  description?: string | null;
}
