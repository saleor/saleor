/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchAttribute
// ====================================================

export interface SearchAttribute_attributes_edges_node {
  __typename: "Attribute";
  id: string;
  slug: string | null;
  name: string | null;
}

export interface SearchAttribute_attributes_edges {
  __typename: "AttributeCountableEdge";
  node: SearchAttribute_attributes_edges_node;
}

export interface SearchAttribute_attributes {
  __typename: "AttributeCountableConnection";
  edges: SearchAttribute_attributes_edges[];
}

export interface SearchAttribute {
  attributes: SearchAttribute_attributes | null;
}

export interface SearchAttributeVariables {
  search: string;
}
