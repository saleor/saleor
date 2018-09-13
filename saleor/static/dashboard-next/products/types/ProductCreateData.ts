/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductCreateData
// ====================================================

export interface ProductCreateData_productTypes_edges_node_productAttributes_edges_node_values {
  __typename: "ProductAttributeValue";
  id: string;
  sortOrder: number;
  name: string | null;
  slug: string | null;
}

export interface ProductCreateData_productTypes_edges_node_productAttributes_edges_node {
  __typename: "ProductAttribute";
  id: string;
  slug: string | null;
  name: string | null;
  values: (ProductCreateData_productTypes_edges_node_productAttributes_edges_node_values | null)[] | null;
}

export interface ProductCreateData_productTypes_edges_node_productAttributes_edges {
  __typename: "ProductAttributeCountableEdge";
  node: ProductCreateData_productTypes_edges_node_productAttributes_edges_node;
}

export interface ProductCreateData_productTypes_edges_node_productAttributes {
  __typename: "ProductAttributeCountableConnection";
  edges: ProductCreateData_productTypes_edges_node_productAttributes_edges[];
}

export interface ProductCreateData_productTypes_edges_node {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  productAttributes: ProductCreateData_productTypes_edges_node_productAttributes | null;
}

export interface ProductCreateData_productTypes_edges {
  __typename: "ProductTypeCountableEdge";
  node: ProductCreateData_productTypes_edges_node;
}

export interface ProductCreateData_productTypes {
  __typename: "ProductTypeCountableConnection";
  edges: ProductCreateData_productTypes_edges[];
}

export interface ProductCreateData_collections_edges_node {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface ProductCreateData_collections_edges {
  __typename: "CollectionCountableEdge";
  node: ProductCreateData_collections_edges_node;
}

export interface ProductCreateData_collections {
  __typename: "CollectionCountableConnection";
  edges: ProductCreateData_collections_edges[];
}

export interface ProductCreateData_categories_edges_node {
  __typename: "Category";
  id: string;
  name: string;
}

export interface ProductCreateData_categories_edges {
  __typename: "CategoryCountableEdge";
  node: ProductCreateData_categories_edges_node;
}

export interface ProductCreateData_categories {
  __typename: "CategoryCountableConnection";
  edges: ProductCreateData_categories_edges[];
}

export interface ProductCreateData {
  productTypes: ProductCreateData_productTypes | null;
  collections: ProductCreateData_collections | null;
  categories: ProductCreateData_categories | null;
}
