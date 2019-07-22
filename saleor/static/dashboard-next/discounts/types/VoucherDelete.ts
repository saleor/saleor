/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VoucherDelete
// ====================================================

export interface VoucherDelete_voucherDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface VoucherDelete_voucherDelete {
  __typename: "VoucherDelete";
  errors: VoucherDelete_voucherDelete_errors[] | null;
}

export interface VoucherDelete {
  voucherDelete: VoucherDelete_voucherDelete | null;
}

export interface VoucherDeleteVariables {
  id: string;
}
