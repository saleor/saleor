/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: ProductDelete
// ====================================================

export interface ProductDelete_productDelete_errors {
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

export interface ProductDelete_productDelete_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface ProductDelete_productDelete {
  __typename: "ProductDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: ProductDelete_productDelete_errors[] | null;
  product: ProductDelete_productDelete_product | null;
}

export interface ProductDelete {
  /**
   * Deletes a product.
   */
  productDelete: ProductDelete_productDelete | null;
}

export interface ProductDeleteVariables {
  id: string;
}
