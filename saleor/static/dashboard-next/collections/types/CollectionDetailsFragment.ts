/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CollectionDetailsFragment
// ====================================================

export interface CollectionDetailsFragment_backgroundImage {
  __typename: "Image";
  url: string;
}

export interface CollectionDetailsFragment {
  __typename: "Collection";
  backgroundImage: CollectionDetailsFragment_backgroundImage | null;
  seoDescription: string | null;
  seoTitle: string | null;
  isPublished: boolean;
}
