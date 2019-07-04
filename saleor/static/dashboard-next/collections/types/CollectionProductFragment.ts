/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CollectionProductFragment
// ====================================================

export interface CollectionProductFragment_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface CollectionProductFragment_thumbnail {
  __typename: "Image";
  url: string;
}

export interface CollectionProductFragment {
  __typename: "Product";
  id: string;
  isPublished: boolean;
  name: string;
  productType: CollectionProductFragment_productType;
  thumbnail: CollectionProductFragment_thumbnail | null;
}
