/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: SaleBulkDelete
// ====================================================

export interface SaleBulkDelete_saleBulkDelete_errors {
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

export interface SaleBulkDelete_saleBulkDelete {
  __typename: "SaleBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: SaleBulkDelete_saleBulkDelete_errors[] | null;
}

export interface SaleBulkDelete {
  /**
   * Deletes sales.
   */
  saleBulkDelete: SaleBulkDelete_saleBulkDelete | null;
}

export interface SaleBulkDeleteVariables {
  ids: (string | null)[];
}
