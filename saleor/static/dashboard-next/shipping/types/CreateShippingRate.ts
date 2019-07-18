/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingPriceInput, ShippingMethodTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CreateShippingRate
// ====================================================

export interface CreateShippingRate_shippingPriceCreate_errors {
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

export interface CreateShippingRate_shippingPriceCreate_shippingZone_countries {
  __typename: "CountryDisplay";
  /**
   * Country code.
   */
  code: string;
  /**
   * Country name.
   */
  country: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_minimumOrderPrice {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_minimumOrderWeight {
  __typename: "Weight";
  /**
   * Weight unit
   */
  unit: string;
  /**
   * Weight value
   */
  value: number;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_maximumOrderPrice {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_maximumOrderWeight {
  __typename: "Weight";
  /**
   * Weight unit
   */
  unit: string;
  /**
   * Weight value
   */
  value: number;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_price {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  minimumOrderPrice: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_minimumOrderPrice | null;
  minimumOrderWeight: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_minimumOrderWeight | null;
  maximumOrderPrice: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_maximumOrderPrice | null;
  maximumOrderWeight: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_maximumOrderWeight | null;
  name: string;
  price: CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods_price | null;
  /**
   * Type of the shipping method.
   */
  type: ShippingMethodTypeEnum | null;
}

export interface CreateShippingRate_shippingPriceCreate_shippingZone {
  __typename: "ShippingZone";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of countries available for the method.
   */
  countries: (CreateShippingRate_shippingPriceCreate_shippingZone_countries | null)[] | null;
  name: string;
  default: boolean;
  /**
   * List of shipping methods available for orders shipped to countries within this shipping zone.
   */
  shippingMethods: (CreateShippingRate_shippingPriceCreate_shippingZone_shippingMethods | null)[] | null;
}

export interface CreateShippingRate_shippingPriceCreate {
  __typename: "ShippingPriceCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CreateShippingRate_shippingPriceCreate_errors[] | null;
  /**
   * A shipping zone to which the shipping method belongs.
   */
  shippingZone: CreateShippingRate_shippingPriceCreate_shippingZone | null;
}

export interface CreateShippingRate {
  /**
   * Creates a new shipping price.
   */
  shippingPriceCreate: CreateShippingRate_shippingPriceCreate | null;
}

export interface CreateShippingRateVariables {
  input: ShippingPriceInput;
}
