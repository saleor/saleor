/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ProductVariantBulkDelete
// ====================================================

export interface ProductVariantBulkDelete_productVariantBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductVariantBulkDelete_productVariantBulkDelete {
  __typename: "ProductVariantBulkDelete";
  errors: ProductVariantBulkDelete_productVariantBulkDelete_errors[] | null;
}

export interface ProductVariantBulkDelete {
  productVariantBulkDelete: ProductVariantBulkDelete_productVariantBulkDelete | null;
}

export interface ProductVariantBulkDeleteVariables {
  ids: string[];
}
