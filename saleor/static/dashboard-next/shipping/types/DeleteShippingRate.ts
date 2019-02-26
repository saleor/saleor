/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: DeleteShippingRate
// ====================================================

export interface DeleteShippingRate_shippingPriceDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface DeleteShippingRate_shippingPriceDelete {
  __typename: "ShippingPriceDelete";
  errors: DeleteShippingRate_shippingPriceDelete_errors[] | null;
}

export interface DeleteShippingRate {
  shippingPriceDelete: DeleteShippingRate_shippingPriceDelete | null;
}

export interface DeleteShippingRateVariables {
  id: string;
}
