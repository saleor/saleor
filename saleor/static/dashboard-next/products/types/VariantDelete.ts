/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: VariantDelete
// ====================================================

export interface VariantDelete_productVariantDelete_errors {
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

export interface VariantDelete_productVariantDelete_productVariant {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface VariantDelete_productVariantDelete {
  __typename: "ProductVariantDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: VariantDelete_productVariantDelete_errors[] | null;
  productVariant: VariantDelete_productVariantDelete_productVariant | null;
}

export interface VariantDelete {
  /**
   * Deletes a product variant.
   */
  productVariantDelete: VariantDelete_productVariantDelete | null;
}

export interface VariantDeleteVariables {
  id: string;
}
