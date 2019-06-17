/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: AttributeBulkDelete
// ====================================================

export interface AttributeBulkDelete_attributeBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AttributeBulkDelete_attributeBulkDelete {
  __typename: "AttributeBulkDelete";
  errors: AttributeBulkDelete_attributeBulkDelete_errors[] | null;
}

export interface AttributeBulkDelete {
  attributeBulkDelete: AttributeBulkDelete_attributeBulkDelete | null;
}

export interface AttributeBulkDeleteVariables {
  ids: string[];
}
