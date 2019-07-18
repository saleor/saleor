/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingMethodTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ShippingMethodFragment
// ====================================================

export interface ShippingMethodFragment_minimumOrderPrice {
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

export interface ShippingMethodFragment_minimumOrderWeight {
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

export interface ShippingMethodFragment_maximumOrderPrice {
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

export interface ShippingMethodFragment_maximumOrderWeight {
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

export interface ShippingMethodFragment_price {
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

export interface ShippingMethodFragment {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  minimumOrderPrice: ShippingMethodFragment_minimumOrderPrice | null;
  minimumOrderWeight: ShippingMethodFragment_minimumOrderWeight | null;
  maximumOrderPrice: ShippingMethodFragment_maximumOrderPrice | null;
  maximumOrderWeight: ShippingMethodFragment_maximumOrderWeight | null;
  name: string;
  price: ShippingMethodFragment_price | null;
  /**
   * Type of the shipping method.
   */
  type: ShippingMethodTypeEnum | null;
}
