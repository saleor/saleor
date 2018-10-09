/* tslint:disable */
// This file was automatically generated and should not be edited.

import { AttributeUpdateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: AttributeUpdate
// ====================================================

export interface AttributeUpdate_attributeUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeUpdate_attributeUpdate {
  __typename: "AttributeUpdate";
  errors: (AttributeUpdate_attributeUpdate_errors | null)[] | null;
}

export interface AttributeUpdate {
  attributeUpdate: AttributeUpdate_attributeUpdate | null;
}

export interface AttributeUpdateVariables {
  id: string;
  input: AttributeUpdateInput;
}
