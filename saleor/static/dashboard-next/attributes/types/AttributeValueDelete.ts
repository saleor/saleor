/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeInputTypeEnum, AttributeValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeValueDelete
// ====================================================

export interface AttributeValueDelete_attributeValueDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeValueDelete_attributeValueDelete_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
  type: AttributeValueType | null;
  value: string | null;
}

export interface AttributeValueDelete_attributeValueDelete_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean;
  filterableInDashboard: boolean;
  filterableInStorefront: boolean;
  inputType: AttributeInputTypeEnum | null;
  storefrontSearchPosition: number;
  valueRequired: boolean;
  values: (AttributeValueDelete_attributeValueDelete_attribute_values | null)[] | null;
}

export interface AttributeValueDelete_attributeValueDelete {
  __typename: "AttributeValueDelete";
  errors: AttributeValueDelete_attributeValueDelete_errors[] | null;
  attribute: AttributeValueDelete_attributeValueDelete_attribute | null;
}

export interface AttributeValueDelete {
  attributeValueDelete: AttributeValueDelete_attributeValueDelete | null;
}

export interface AttributeValueDeleteVariables {
  id: string;
}
