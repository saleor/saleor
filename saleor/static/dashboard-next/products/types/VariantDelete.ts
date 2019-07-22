/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VariantDelete
// ====================================================

export interface VariantDelete_productVariantDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface VariantDelete_productVariantDelete_productVariant {
  __typename: "ProductVariant";
  id: string;
}

export interface VariantDelete_productVariantDelete {
  __typename: "ProductVariantDelete";
  errors: VariantDelete_productVariantDelete_errors[] | null;
  productVariant: VariantDelete_productVariantDelete_productVariant | null;
}

export interface VariantDelete {
  productVariantDelete: VariantDelete_productVariantDelete | null;
}

export interface VariantDeleteVariables {
  id: string;
}
