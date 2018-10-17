/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CollectionFragment
// ====================================================

export interface CollectionFragment_products {
  __typename: "ProductCountableConnection";
  totalCount: number | null;
}

export interface CollectionFragment {
  __typename: "Collection";
  id: string;
  isPublished: boolean;
  name: string;
  products: CollectionFragment_products | null;
}
