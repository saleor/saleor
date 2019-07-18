/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ProductTypeBulkDelete
// ====================================================

export interface ProductTypeBulkDelete_productTypeBulkDelete_errors {
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

export interface ProductTypeBulkDelete_productTypeBulkDelete {
  __typename: "ProductTypeBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ProductTypeBulkDelete_productTypeBulkDelete_errors[] | null;
}

export interface ProductTypeBulkDelete {
  /**
   * Deletes product types.
   */
  productTypeBulkDelete: ProductTypeBulkDelete_productTypeBulkDelete | null;
}

export interface ProductTypeBulkDeleteVariables {
  ids: (string | null)[];
}
