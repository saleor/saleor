/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingMethodTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: DeleteShippingRate
// ====================================================

export interface DeleteShippingRate_shippingPriceDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_minimumOrderPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_minimumOrderWeight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_maximumOrderPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_maximumOrderWeight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods {
  __typename: "ShippingMethod";
  id: string;
  minimumOrderPrice: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_minimumOrderPrice | null;
  minimumOrderWeight: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_minimumOrderWeight | null;
  maximumOrderPrice: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_maximumOrderPrice | null;
  maximumOrderWeight: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_maximumOrderWeight | null;
  name: string;
  price: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_price | null;
  type: ShippingMethodTypeEnum | null;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone {
  __typename: "ShippingZone";
  id: string;
  countries: (DeleteShippingRate_shippingPriceDelete_shippingZone_countries | null)[] | null;
  name: string;
  default: boolean;
  shippingMethods: (DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods | null)[] | null;
}

export interface DeleteShippingRate_shippingPriceDelete {
  __typename: "ShippingPriceDelete";
  errors: DeleteShippingRate_shippingPriceDelete_errors[] | null;
  shippingZone: DeleteShippingRate_shippingPriceDelete_shippingZone | null;
}

export interface DeleteShippingRate {
  shippingPriceDelete: DeleteShippingRate_shippingPriceDelete | null;
}

export interface DeleteShippingRateVariables {
  id: string;
}
