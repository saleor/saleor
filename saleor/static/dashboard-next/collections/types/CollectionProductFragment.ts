/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CollectionProductFragment
// ====================================================

export interface CollectionProductFragment_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface CollectionProductFragment_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface CollectionProductFragment {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  isPublished: boolean;
  name: string;
  productType: CollectionProductFragment_productType;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: CollectionProductFragment_thumbnail | null;
}
