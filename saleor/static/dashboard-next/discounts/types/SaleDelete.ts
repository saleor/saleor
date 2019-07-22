/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: SaleDelete
// ====================================================

export interface SaleDelete_saleDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface SaleDelete_saleDelete {
  __typename: "SaleDelete";
  errors: SaleDelete_saleDelete_errors[] | null;
}

export interface SaleDelete {
  saleDelete: SaleDelete_saleDelete | null;
}

export interface SaleDeleteVariables {
  id: string;
}
