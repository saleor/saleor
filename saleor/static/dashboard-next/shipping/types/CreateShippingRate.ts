/* tslint:disable */
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

export interface CreateShippingRate_shippingPriceCreate_shippingMethod_minimumOrderPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingMethod_minimumOrderWeight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface CreateShippingRate_shippingPriceCreate_shippingMethod_maximumOrderPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingMethod_maximumOrderWeight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface CreateShippingRate_shippingPriceCreate_shippingMethod_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
  minimumOrderPrice: CreateShippingRate_shippingPriceCreate_shippingMethod_minimumOrderPrice | null;
  minimumOrderWeight: CreateShippingRate_shippingPriceCreate_shippingMethod_minimumOrderWeight | null;
  maximumOrderPrice: CreateShippingRate_shippingPriceCreate_shippingMethod_maximumOrderPrice | null;
  maximumOrderWeight: CreateShippingRate_shippingPriceCreate_shippingMethod_maximumOrderWeight | null;
  name: string;
  price: CreateShippingRate_shippingPriceCreate_shippingMethod_price | null;
  type: ShippingMethodTypeEnum | null;
}

export interface CreateShippingRate_shippingPriceCreate {
  __typename: "ShippingPriceCreate";
  errors: CreateShippingRate_shippingPriceCreate_errors[] | null;
  shippingMethod: CreateShippingRate_shippingPriceCreate_shippingMethod | null;
}

export interface CreateShippingRate {
  shippingPriceCreate: CreateShippingRate_shippingPriceCreate | null;
}

export interface CreateShippingRateVariables {
  input: ShippingPriceInput;
}
