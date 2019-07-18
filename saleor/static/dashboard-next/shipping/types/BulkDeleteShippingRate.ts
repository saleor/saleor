/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: BulkDeleteShippingRate
// ====================================================

export interface BulkDeleteShippingRate_shippingPriceBulkDelete_errors {
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

export interface BulkDeleteShippingRate_shippingPriceBulkDelete {
  __typename: "ShippingPriceBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: BulkDeleteShippingRate_shippingPriceBulkDelete_errors[] | null;
}

export interface BulkDeleteShippingRate {
  /**
   * Deletes shipping prices.
   */
  shippingPriceBulkDelete: BulkDeleteShippingRate_shippingPriceBulkDelete | null;
}

export interface BulkDeleteShippingRateVariables {
  ids: (string | null)[];
}
