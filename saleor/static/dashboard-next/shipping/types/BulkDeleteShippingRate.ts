/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: BulkDeleteShippingRate
// ====================================================

export interface BulkDeleteShippingRate_shippingPriceBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface BulkDeleteShippingRate_shippingPriceBulkDelete {
  __typename: "ShippingPriceBulkDelete";
  errors: BulkDeleteShippingRate_shippingPriceBulkDelete_errors[] | null;
}

export interface BulkDeleteShippingRate {
  shippingPriceBulkDelete: BulkDeleteShippingRate_shippingPriceBulkDelete | null;
}

export interface BulkDeleteShippingRateVariables {
  ids: (string | null)[];
}
