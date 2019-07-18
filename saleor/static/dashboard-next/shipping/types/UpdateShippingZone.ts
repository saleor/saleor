/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingZoneInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateShippingZone
// ====================================================

export interface UpdateShippingZone_shippingZoneUpdate_errors {
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

export interface UpdateShippingZone_shippingZoneUpdate_shippingZone_countries {
  __typename: "CountryDisplay";
  /**
   * Country name.
   */
  country: string;
  /**
   * Country code.
   */
  code: string;
}

export interface UpdateShippingZone_shippingZoneUpdate_shippingZone {
  __typename: "ShippingZone";
  /**
   * List of countries available for the method.
   */
  countries: (UpdateShippingZone_shippingZoneUpdate_shippingZone_countries | null)[] | null;
  default: boolean;
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface UpdateShippingZone_shippingZoneUpdate {
  __typename: "ShippingZoneUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UpdateShippingZone_shippingZoneUpdate_errors[] | null;
  shippingZone: UpdateShippingZone_shippingZoneUpdate_shippingZone | null;
}

export interface UpdateShippingZone {
  /**
   * Updates a new shipping zone.
   */
  shippingZoneUpdate: UpdateShippingZone_shippingZoneUpdate | null;
}

export interface UpdateShippingZoneVariables {
  id: string;
  input: ShippingZoneInput;
}
