/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ProductTypeDelete
// ====================================================

export interface ProductTypeDelete_productTypeDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface ProductTypeDelete_productTypeDelete_productType {
  __typename: "ProductType";
  id: string;
}

export interface ProductTypeDelete_productTypeDelete {
  __typename: "ProductTypeDelete";
  errors: ProductTypeDelete_productTypeDelete_errors[] | null;
  productType: ProductTypeDelete_productTypeDelete_productType | null;
}

export interface ProductTypeDelete {
  productTypeDelete: ProductTypeDelete_productTypeDelete | null;
}

export interface ProductTypeDeleteVariables {
  id: string;
}
