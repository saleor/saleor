/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ProductDelete
// ====================================================

export interface ProductDelete_productDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductDelete_productDelete_product {
  __typename: "Product";
  id: string;
}

export interface ProductDelete_productDelete {
  __typename: "ProductDelete";
  errors: ProductDelete_productDelete_errors[] | null;
  product: ProductDelete_productDelete_product | null;
}

export interface ProductDelete {
  productDelete: ProductDelete_productDelete | null;
}

export interface ProductDeleteVariables {
  id: string;
}
