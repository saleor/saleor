/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VoucherBulkDelete
// ====================================================

export interface VoucherBulkDelete_voucherBulkDelete_errors {
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

export interface VoucherBulkDelete_voucherBulkDelete {
  __typename: "VoucherBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: VoucherBulkDelete_voucherBulkDelete_errors[] | null;
}

export interface VoucherBulkDelete {
  /**
   * Deletes vouchers.
   */
  voucherBulkDelete: VoucherBulkDelete_voucherBulkDelete | null;
}

export interface VoucherBulkDeleteVariables {
  ids: (string | null)[];
}
