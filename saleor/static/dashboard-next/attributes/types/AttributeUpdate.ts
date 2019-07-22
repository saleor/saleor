/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AttributeUpdateInput, AttributeInputTypeEnum, AttributeValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeUpdate
// ====================================================

export interface AttributeUpdate_attributeUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeUpdate_attributeUpdate_attribute_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
  sortOrder: number;
  type: AttributeValueType | null;
  value: string | null;
}

export interface AttributeUpdate_attributeUpdate_attribute {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  visibleInStorefront: boolean | null;
  filterableInDashboard: boolean | null;
  filterableInStorefront: boolean | null;
  inputType: AttributeInputTypeEnum | null;
  storefrontSearchPosition: number | null;
  valueRequired: boolean | null;
  values: (AttributeUpdate_attributeUpdate_attribute_values | null)[] | null;
}

export interface AttributeUpdate_attributeUpdate {
  __typename: "AttributeUpdate";
  errors: AttributeUpdate_attributeUpdate_errors[] | null;
  attribute: AttributeUpdate_attributeUpdate_attribute | null;
}

export interface AttributeUpdate {
  attributeUpdate: AttributeUpdate_attributeUpdate | null;
}

export interface AttributeUpdateVariables {
  id: string;
  input: AttributeUpdateInput;
}
