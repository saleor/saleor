/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CategoryDetails
// ====================================================

export interface CategoryDetails_category_parent {
  __typename: "Category";
  id: string;
}

export interface CategoryDetails_category {
  __typename: "Category";
  id: string;
  name: string;
  description: string;
  parent: CategoryDetails_category_parent | null;
}

export interface CategoryDetails {
  category: CategoryDetails_category | null;
}

export interface CategoryDetailsVariables {
  id: string;
}
