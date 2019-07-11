/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueCreateInput, AttributeInputTypeEnum, AttributeValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeValueCreate
// ====================================================

export interface AttributeValueCreate_attributeValueCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeValueCreate_attributeValueCreate_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
  sortOrder: number | null;
  type: AttributeValueType | null;
  value: string | null;
}

export interface AttributeValueCreate_attributeValueCreate_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean | null;
  filterableInDashboard: boolean | null;
  filterableInStorefront: boolean | null;
  inputType: AttributeInputTypeEnum | null;
  storefrontSearchPosition: number | null;
  values: (AttributeValueCreate_attributeValueCreate_attribute_values | null)[] | null;
}

export interface AttributeValueCreate_attributeValueCreate {
  __typename: "AttributeValueCreate";
  errors: AttributeValueCreate_attributeValueCreate_errors[] | null;
  attribute: AttributeValueCreate_attributeValueCreate_attribute | null;
}

export interface AttributeValueCreate {
  attributeValueCreate: AttributeValueCreate_attributeValueCreate | null;
}

export interface AttributeValueCreateVariables {
  id: string;
  input: AttributeValueCreateInput;
}
