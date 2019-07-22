/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AttributeFragment
// ====================================================

export interface AttributeFragment_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface AttributeFragment {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (AttributeFragment_values | null)[] | null;
}
