/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: productBulkDelete
// ====================================================

export interface productBulkDelete_productBulkDelete_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface productBulkDelete_productBulkDelete {
  __typename: "ProductBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: productBulkDelete_productBulkDelete_errors[] | null;
}

export interface productBulkDelete {
  /**
   * Deletes products.
   */
  productBulkDelete: productBulkDelete_productBulkDelete | null;
}

export interface productBulkDeleteVariables {
  ids: string[];
}
