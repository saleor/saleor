/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ProductTypeDelete
// ====================================================

export interface ProductTypeDelete_productTypeDelete_errors {
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

export interface ProductTypeDelete_productTypeDelete_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface ProductTypeDelete_productTypeDelete {
  __typename: "ProductTypeDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ProductTypeDelete_productTypeDelete_errors[] | null;
  productType: ProductTypeDelete_productTypeDelete_productType | null;
}

export interface ProductTypeDelete {
  /**
   * Deletes a product type.
   */
  productTypeDelete: ProductTypeDelete_productTypeDelete | null;
}

export interface ProductTypeDeleteVariables {
  id: string;
}
