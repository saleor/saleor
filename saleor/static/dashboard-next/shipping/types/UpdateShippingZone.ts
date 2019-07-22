/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingZoneInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateShippingZone
// ====================================================

export interface UpdateShippingZone_shippingZoneUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateShippingZone_shippingZoneUpdate_shippingZone_countries {
  __typename: "CountryDisplay";
  country: string;
  code: string;
}

export interface UpdateShippingZone_shippingZoneUpdate_shippingZone {
  __typename: "ShippingZone";
  countries: (UpdateShippingZone_shippingZoneUpdate_shippingZone_countries | null)[] | null;
  default: boolean;
  id: string;
  name: string;
}

export interface UpdateShippingZone_shippingZoneUpdate {
  __typename: "ShippingZoneUpdate";
  errors: UpdateShippingZone_shippingZoneUpdate_errors[] | null;
  shippingZone: UpdateShippingZone_shippingZoneUpdate_shippingZone | null;
}

export interface UpdateShippingZone {
  shippingZoneUpdate: UpdateShippingZone_shippingZoneUpdate | null;
}

export interface UpdateShippingZoneVariables {
  id: string;
  input: ShippingZoneInput;
}
