/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchProducts
// ====================================================

export interface SearchProducts_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface SearchProducts_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface SearchProducts_products_edges_node {
  __typename: "Product";
  id: string;
  isPublished: boolean;
  name: string;
  productType: SearchProducts_products_edges_node_productType;
  thumbnail: SearchProducts_products_edges_node_thumbnail | null;
}

export interface SearchProducts_products_edges {
  __typename: "ProductCountableEdge";
  node: SearchProducts_products_edges_node;
}

export interface SearchProducts_products {
  __typename: "ProductCountableConnection";
  edges: SearchProducts_products_edges[];
}

export interface SearchProducts {
  products: SearchProducts_products | null;
}

export interface SearchProductsVariables {
  query: string;
}
