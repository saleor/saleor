/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AttributeDetailsFragment
// ====================================================

export interface AttributeDetailsFragment_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
  sortOrder: number | null;
  type: AttributeValueType | null;
  value: string | null;
}

export interface AttributeDetailsFragment {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (AttributeDetailsFragment_values | null)[] | null;
}
