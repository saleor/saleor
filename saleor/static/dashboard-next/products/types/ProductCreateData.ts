/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductCreateData
// ====================================================

export interface ProductCreateData_productTypes_edges_node_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  sortOrder: number;
  name: string | null;
  slug: string | null;
}

export interface ProductCreateData_productTypes_edges_node_productAttributes {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
  values: (ProductCreateData_productTypes_edges_node_productAttributes_values | null)[] | null;
}

export interface ProductCreateData_productTypes_edges_node {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  productAttributes: (ProductCreateData_productTypes_edges_node_productAttributes | null)[] | null;
}

export interface ProductCreateData_productTypes_edges {
  __typename: "ProductTypeCountableEdge";
  node: ProductCreateData_productTypes_edges_node;
}

export interface ProductCreateData_productTypes {
  __typename: "ProductTypeCountableConnection";
  edges: ProductCreateData_productTypes_edges[];
}

export interface ProductCreateData {
  productTypes: ProductCreateData_productTypes | null;
}
