/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeValueCreateInput, AttributeInputTypeEnum, AttributeValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeValueUpdate
// ====================================================

export interface AttributeValueUpdate_attributeValueUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeValueUpdate_attributeValueUpdate_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
  sortOrder: number | null;
  type: AttributeValueType | null;
  value: string | null;
}

export interface AttributeValueUpdate_attributeValueUpdate_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean | null;
  filterableInDashboard: boolean | null;
  filterableInStorefront: boolean | null;
  inputType: AttributeInputTypeEnum | null;
  storefrontSearchPosition: number | null;
  values: (AttributeValueUpdate_attributeValueUpdate_attribute_values | null)[] | null;
}

export interface AttributeValueUpdate_attributeValueUpdate {
  __typename: "AttributeValueUpdate";
  errors: AttributeValueUpdate_attributeValueUpdate_errors[] | null;
  attribute: AttributeValueUpdate_attributeValueUpdate_attribute | null;
}

export interface AttributeValueUpdate {
  attributeValueUpdate: AttributeValueUpdate_attributeValueUpdate | null;
}

export interface AttributeValueUpdateVariables {
  id: string;
  input: AttributeValueCreateInput;
}
