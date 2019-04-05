/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingPriceInput, ShippingMethodTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CreateShippingRate
// ====================================================

export interface CreateShippingRate_shippingPriceCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_minimumOrderPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_minimumOrderWeight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_maximumOrderPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_maximumOrderWeight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods {
  __typename: "ShippingMethod";
  id: string;
  minimumOrderPrice: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_minimumOrderPrice | null;
  minimumOrderWeight: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_minimumOrderWeight | null;
  maximumOrderPrice: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_maximumOrderPrice | null;
  maximumOrderWeight: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_maximumOrderWeight | null;
  name: string;
  price: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_price | null;
  type: ShippingMethodTypeEnum | null;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone {
  __typename: "ShippingZone";
  id: string;
  countries: (CreateShippingRate_shippingPriceCreate_shippingZone_countries | null)[] | null;
  name: string;
  default: boolean;
  shippingMethods: (CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods | null)[] | null;
}

export interface CreateShippingRate_shippingPriceCreate {
  __typename: "ShippingPriceCreate";
  errors: CreateShippingRate_shippingPriceCreate_errors[] | null;
  shippingZone: CreateShippingRate_shippingPriceCreate_shippingZone | null;
}

export interface CreateShippingRate {
  shippingPriceCreate: CreateShippingRate_shippingPriceCreate | null;
}

export interface CreateShippingRateVariables {
  input: ShippingPriceInput;
}
