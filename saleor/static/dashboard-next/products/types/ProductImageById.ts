/* tslint:disable */
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

export interface ProductImageById_product_images_edges_node {
  __typename: "ProductImage";
  id: string;
  url: string;
}

export interface ProductImageById_product_images_edges {
  __typename: "ProductImageCountableEdge";
  node: ProductImageById_product_images_edges_node;
}

export interface ProductImageById_product_images_pageInfo {
  __typename: "PageInfo";
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface ProductImageById_product_images {
  __typename: "ProductImageCountableConnection";
  edges: ProductImageById_product_images_edges[];
  pageInfo: ProductImageById_product_images_pageInfo;
}

export interface ProductImageById_product {
  __typename: "Product";
  id: string;
  mainImage: ProductImageById_product_mainImage | null;
  images: ProductImageById_product_images | null;
}

export interface ProductImageById {
  product: ProductImageById_product | null;
}

export interface ProductImageByIdVariables {
  productId: string;
  imageId: string;
}
