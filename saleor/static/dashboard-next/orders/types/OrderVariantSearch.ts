/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: OrderVariantSearch
// ====================================================

export interface OrderVariantSearch_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderVariantSearch_products_edges_node_variants_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderVariantSearch_products_edges_node_variants {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  price: OrderVariantSearch_products_edges_node_variants_price | null;
}

export interface OrderVariantSearch_products_edges_node {
  __typename: "Product";
  id: string;
  name: string;
  thumbnail: OrderVariantSearch_products_edges_node_thumbnail | null;
  variants: (OrderVariantSearch_products_edges_node_variants | null)[] | null;
}

export interface OrderVariantSearch_products_edges {
  __typename: "ProductCountableEdge";
  node: OrderVariantSearch_products_edges_node;
}

export interface OrderVariantSearch_products {
  __typename: "ProductCountableConnection";
  edges: OrderVariantSearch_products_edges[];
}

export interface OrderVariantSearch {
  products: OrderVariantSearch_products | null;
}

export interface OrderVariantSearchVariables {
  search: string;
}
