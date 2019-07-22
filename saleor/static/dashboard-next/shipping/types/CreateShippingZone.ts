/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingZoneInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CreateShippingZone
// ====================================================

export interface CreateShippingZone_shippingZoneCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CreateShippingZone_shippingZoneCreate_shippingZone_countries {
  __typename: "CountryDisplay";
  country: string;
  code: string;
}

export interface CreateShippingZone_shippingZoneCreate_shippingZone {
  __typename: "ShippingZone";
  countries: (CreateShippingZone_shippingZoneCreate_shippingZone_countries | null)[] | null;
  default: boolean;
  id: string;
  name: string;
}

export interface CreateShippingZone_shippingZoneCreate {
  __typename: "ShippingZoneCreate";
  errors: CreateShippingZone_shippingZoneCreate_errors[] | null;
  shippingZone: CreateShippingZone_shippingZoneCreate_shippingZone | null;
}

export interface CreateShippingZone {
  shippingZoneCreate: CreateShippingZone_shippingZoneCreate | null;
}

export interface CreateShippingZoneVariables {
  input: ShippingZoneInput;
}
