/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingPriceInput, ShippingMethodTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateShippingRate
// ====================================================

export interface UpdateShippingRate_shippingPriceUpdate_errors {
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

export interface UpdateShippingRate_shippingPriceUpdate_shippingMethod_minimumOrderPrice {
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

export interface UpdateShippingRate_shippingPriceUpdate_shippingMethod_minimumOrderWeight {
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

export interface UpdateShippingRate_shippingPriceUpdate_shippingMethod_maximumOrderPrice {
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

export interface UpdateShippingRate_shippingPriceUpdate_shippingMethod_maximumOrderWeight {
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

export interface UpdateShippingRate_shippingPriceUpdate_shippingMethod_price {
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

export interface UpdateShippingRate_shippingPriceUpdate_shippingMethod {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  minimumOrderPrice: UpdateShippingRate_shippingPriceUpdate_shippingMethod_minimumOrderPrice | null;
  minimumOrderWeight: UpdateShippingRate_shippingPriceUpdate_shippingMethod_minimumOrderWeight | null;
  maximumOrderPrice: UpdateShippingRate_shippingPriceUpdate_shippingMethod_maximumOrderPrice | null;
  maximumOrderWeight: UpdateShippingRate_shippingPriceUpdate_shippingMethod_maximumOrderWeight | null;
  name: string;
  price: UpdateShippingRate_shippingPriceUpdate_shippingMethod_price | null;
  /**
   * Type of the shipping method.
   */
  type: ShippingMethodTypeEnum | null;
}

export interface UpdateShippingRate_shippingPriceUpdate {
  __typename: "ShippingPriceUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UpdateShippingRate_shippingPriceUpdate_errors[] | null;
  shippingMethod: UpdateShippingRate_shippingPriceUpdate_shippingMethod | null;
}

export interface UpdateShippingRate {
  /**
   * Updates a new shipping price.
   */
  shippingPriceUpdate: UpdateShippingRate_shippingPriceUpdate | null;
}

export interface UpdateShippingRateVariables {
  id: string;
  input: ShippingPriceInput;
}
