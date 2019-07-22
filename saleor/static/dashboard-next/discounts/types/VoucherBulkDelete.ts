/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VoucherBulkDelete
// ====================================================

export interface VoucherBulkDelete_voucherBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface VoucherBulkDelete_voucherBulkDelete {
  __typename: "VoucherBulkDelete";
  errors: VoucherBulkDelete_voucherBulkDelete_errors[] | null;
}

export interface VoucherBulkDelete {
  voucherBulkDelete: VoucherBulkDelete_voucherBulkDelete | null;
}

export interface VoucherBulkDeleteVariables {
  ids: (string | null)[];
}
