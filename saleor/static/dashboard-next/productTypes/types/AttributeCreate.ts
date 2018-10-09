/* tslint:disable */
// This file was automatically generated and should not be edited.

import { AttributeCreateInput, AttributeTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeCreate
// ====================================================

export interface AttributeCreate_attributeCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeCreate_attributeCreate {
  __typename: "AttributeCreate";
  errors: (AttributeCreate_attributeCreate_errors | null)[] | null;
}

export interface AttributeCreate {
  attributeCreate: AttributeCreate_attributeCreate | null;
}

export interface AttributeCreateVariables {
  id: string;
  input: AttributeCreateInput;
  type: AttributeTypeEnum;
}
