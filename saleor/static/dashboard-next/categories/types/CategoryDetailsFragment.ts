/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CategoryDetailsFragment
// ====================================================

export interface CategoryDetailsFragment_backgroundImage {
  __typename: "Image";
  alt: string | null;
  url: string;
}

export interface CategoryDetailsFragment_parent {
  __typename: "Category";
  id: string;
}

export interface CategoryDetailsFragment {
  __typename: "Category";
  id: string;
  backgroundImage: CategoryDetailsFragment_backgroundImage | null;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  parent: CategoryDetailsFragment_parent | null;
}
