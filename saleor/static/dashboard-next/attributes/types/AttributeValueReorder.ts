/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ReorderInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeValueReorder
// ====================================================

export interface AttributeValueReorder_attributeReorderValues_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeValueReorder_attributeReorderValues_attribute_values {
  __typename: "AttributeValue";
  id: string;
}

export interface AttributeValueReorder_attributeReorderValues_attribute {
  __typename: "Attribute";
  id: string;
  values: (AttributeValueReorder_attributeReorderValues_attribute_values | null)[] | null;
}

export interface AttributeValueReorder_attributeReorderValues {
  __typename: "AttributeReorderValues";
  errors: AttributeValueReorder_attributeReorderValues_errors[] | null;
  attribute: AttributeValueReorder_attributeReorderValues_attribute | null;
}

export interface AttributeValueReorder {
  attributeReorderValues: AttributeValueReorder_attributeReorderValues | null;
}

export interface AttributeValueReorderVariables {
  id: string;
  move: ReorderInput;
}
