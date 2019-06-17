/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: AttributeDelete
// ====================================================

export interface AttributeDelete_attributeDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeDelete_attributeDelete {
  __typename: "AttributeDelete";
  errors: AttributeDelete_attributeDelete_errors[] | null;
}

export interface AttributeDelete {
  attributeDelete: AttributeDelete_attributeDelete | null;
}

export interface AttributeDeleteVariables {
  id: string;
}
