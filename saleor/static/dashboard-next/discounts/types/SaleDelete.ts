/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: SaleDelete
// ====================================================

export interface SaleDelete_saleDelete_errors {
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

export interface SaleDelete_saleDelete {
  __typename: "SaleDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: SaleDelete_saleDelete_errors[] | null;
}

export interface SaleDelete {
  /**
   * Deletes a sale.
   */
  saleDelete: SaleDelete_saleDelete | null;
}

export interface SaleDeleteVariables {
  id: string;
}
