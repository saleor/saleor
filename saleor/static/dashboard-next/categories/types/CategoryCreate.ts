/* tslint:disable */
// This file was automatically generated and should not be edited.

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
  name?: string | null;
  description?: string | null;
  parent?: string | null;
}
