/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductImageById
// ====================================================

export interface ProductImageById_product_mainImage {
  __typename: "ProductImage";
  /**
   * The ID of the object.
   */
  id: string;
  alt: string;
  /**
   * The URL of the image.
   */
  url: string;
}

export interface ProductImageById_product_images {
  __typename: "ProductImage";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * The URL of the image.
   */
  url: string;
}

export interface ProductImageById_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Get a single product image by ID
   */
  mainImage: ProductImageById_product_mainImage | null;
  /**
   * List of images for the product
   */
  images: (ProductImageById_product_images | null)[] | null;
}

export interface ProductImageById {
  /**
   * Lookup a product by ID.
   */
  product: ProductImageById_product | null;
}

export interface ProductImageByIdVariables {
  productId: string;
  imageId: string;
}
