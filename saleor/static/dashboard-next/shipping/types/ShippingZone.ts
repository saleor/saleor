/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingMethodTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ShippingZone
// ====================================================

export interface ShippingZone_shippingZone_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface ShippingZone_shippingZone_shippingMethods_minimumOrderPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ShippingZone_shippingZone_shippingMethods_minimumOrderWeight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface ShippingZone_shippingZone_shippingMethods_maximumOrderPrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ShippingZone_shippingZone_shippingMethods_maximumOrderWeight {
  __typename: "Weight";
  unit: string;
  value: number;
}

export interface ShippingZone_shippingZone_shippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ShippingZone_shippingZone_shippingMethods {
  __typename: "ShippingMethod";
  id: string;
  minimumOrderPrice: ShippingZone_shippingZone_shippingMethods_minimumOrderPrice | null;
  minimumOrderWeight: ShippingZone_shippingZone_shippingMethods_minimumOrderWeight | null;
  maximumOrderPrice: ShippingZone_shippingZone_shippingMethods_maximumOrderPrice | null;
  maximumOrderWeight: ShippingZone_shippingZone_shippingMethods_maximumOrderWeight | null;
  name: string;
  price: ShippingZone_shippingZone_shippingMethods_price | null;
  type: ShippingMethodTypeEnum | null;
}

export interface ShippingZone_shippingZone {
  __typename: "ShippingZone";
  id: string;
  countries: (ShippingZone_shippingZone_countries | null)[] | null;
  name: string;
  default: boolean;
  shippingMethods: (ShippingZone_shippingZone_shippingMethods | null)[] | null;
}

export interface ShippingZone {
  shippingZone: ShippingZone_shippingZone | null;
}

export interface ShippingZoneVariables {
  id: string;
}
