/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingMethodTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: DeleteShippingRate
// ====================================================

export interface DeleteShippingRate_shippingPriceDelete_errors {
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

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_countries {
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

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_minimumOrderPrice {
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

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_minimumOrderWeight {
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

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_maximumOrderPrice {
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

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_maximumOrderWeight {
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

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_price {
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

export interface DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  minimumOrderPrice: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_minimumOrderPrice | null;
  minimumOrderWeight: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_minimumOrderWeight | null;
  maximumOrderPrice: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_maximumOrderPrice | null;
  maximumOrderWeight: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_maximumOrderWeight | null;
  name: string;
  price: DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods_price | null;
  /**
   * Type of the shipping method.
   */
  type: ShippingMethodTypeEnum | null;
}

export interface DeleteShippingRate_shippingPriceDelete_shippingZone {
  __typename: "ShippingZone";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of countries available for the method.
   */
  countries: (DeleteShippingRate_shippingPriceDelete_shippingZone_countries | null)[] | null;
  name: string;
  default: boolean;
  /**
   * List of shipping methods available for orders shipped to countries within this shipping zone.
   */
  shippingMethods: (DeleteShippingRate_shippingPriceDelete_shippingZone_shippingMethods | null)[] | null;
}

export interface DeleteShippingRate_shippingPriceDelete {
  __typename: "ShippingPriceDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: DeleteShippingRate_shippingPriceDelete_errors[] | null;
  /**
   * A shipping zone to which the shipping method belongs.
   */
  shippingZone: DeleteShippingRate_shippingPriceDelete_shippingZone | null;
}

export interface DeleteShippingRate {
  /**
   * Deletes a shipping price.
   */
  shippingPriceDelete: DeleteShippingRate_shippingPriceDelete | null;
}

export interface DeleteShippingRateVariables {
  id: string;
}
