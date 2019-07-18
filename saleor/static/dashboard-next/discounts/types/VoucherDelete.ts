/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VoucherDelete
// ====================================================

export interface VoucherDelete_voucherDelete_errors {
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

export interface VoucherDelete_voucherDelete {
  __typename: "VoucherDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: VoucherDelete_voucherDelete_errors[] | null;
}

export interface VoucherDelete {
  /**
   * Deletes a voucher.
   */
  voucherDelete: VoucherDelete_voucherDelete | null;
}

export interface VoucherDeleteVariables {
  id: string;
}
