/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CategoryDetailsFragment
// ====================================================

export interface CategoryDetailsFragment_parent {
  __typename: "Category";
  id: string;
}

export interface CategoryDetailsFragment {
  __typename: "Category";
  id: string;
  name: string;
  description: string;
  seoDescription: string | null;
  seoTitle: string | null;
  parent: CategoryDetailsFragment_parent | null;
}
