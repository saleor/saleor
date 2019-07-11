/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeCreateInput, AttributeInputTypeEnum, AttributeValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeCreate
// ====================================================

export interface AttributeCreate_attributeCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeCreate_attributeCreate_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
  sortOrder: number | null;
  type: AttributeValueType | null;
  value: string | null;
}

export interface AttributeCreate_attributeCreate_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean | null;
  filterableInDashboard: boolean | null;
  filterableInStorefront: boolean | null;
  inputType: AttributeInputTypeEnum | null;
  storefrontSearchPosition: number | null;
  values: (AttributeCreate_attributeCreate_attribute_values | null)[] | null;
}

export interface AttributeCreate_attributeCreate {
  __typename: "AttributeCreate";
  errors: AttributeCreate_attributeCreate_errors[] | null;
  attribute: AttributeCreate_attributeCreate_attribute | null;
}

export interface AttributeCreate {
  attributeCreate: AttributeCreate_attributeCreate | null;
}

export interface AttributeCreateVariables {
  input: AttributeCreateInput;
}
