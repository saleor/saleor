/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchProducts
// ====================================================

export interface SearchProducts_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface SearchProducts_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: SearchProducts_products_edges_node_thumbnail | null;
}

export interface SearchProducts_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SearchProducts_products_edges_node;
}

export interface SearchProducts_products {
  __typename: "ProductCountableConnection";
  edges: SearchProducts_products_edges[];
}

export interface SearchProducts {
  /**
   * List of the shop's products.
   */
  products: SearchProducts_products | null;
}

export interface SearchProductsVariables {
  after?: string | null;
  first: number;
  query: string;
}
