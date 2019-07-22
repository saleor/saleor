/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductImageById
// ====================================================

export interface ProductImageById_product_mainImage {
  __typename: "ProductImage";
  id: string;
  alt: string;
  url: string;
}

export interface ProductImageById_product_images {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductImageById_product {
  __typename: "Product";
  id: string;
  name: string;
  mainImage: ProductImageById_product_mainImage | null;
  images: (ProductImageById_product_images | null)[] | null;
}

export interface ProductImageById {
  product: ProductImageById_product | null;
}

export interface ProductImageByIdVariables {
  productId: string;
  imageId: string;
}
