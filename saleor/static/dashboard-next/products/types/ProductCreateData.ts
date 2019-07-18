/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductCreateData
// ====================================================

export interface ProductCreateData_productTypes_edges_node_productAttributes_values {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  sortOrder: number | null;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of a value (unique per attribute).
   */
  slug: string | null;
}

export interface ProductCreateData_productTypes_edges_node_productAttributes {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Internal representation of an attribute name.
   */
  slug: string | null;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * List of attribute's values.
   */
  values: (ProductCreateData_productTypes_edges_node_productAttributes_values | null)[] | null;
}

export interface ProductCreateData_productTypes_edges_node {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  hasVariants: boolean;
  /**
   * Product attributes of that product type.
   */
  productAttributes: (ProductCreateData_productTypes_edges_node_productAttributes | null)[] | null;
}

export interface ProductCreateData_productTypes_edges {
  __typename: "ProductTypeCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: ProductCreateData_productTypes_edges_node;
}

export interface ProductCreateData_productTypes {
  __typename: "ProductTypeCountableConnection";
  edges: ProductCreateData_productTypes_edges[];
}

export interface ProductCreateData {
  /**
   * List of the shop's product types.
   */
  productTypes: ProductCreateData_productTypes | null;
}
