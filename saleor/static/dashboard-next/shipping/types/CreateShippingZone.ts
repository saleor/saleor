/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ShippingZoneInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CreateShippingZone
// ====================================================

export interface CreateShippingZone_shippingZoneCreate_errors {
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

export interface CreateShippingZone_shippingZoneCreate_shippingZone_countries {
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

export interface CreateShippingZone_shippingZoneCreate_shippingZone {
  __typename: "ShippingZone";
  /**
   * List of countries available for the method.
   */
  countries: (CreateShippingZone_shippingZoneCreate_shippingZone_countries | null)[] | null;
  default: boolean;
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface CreateShippingZone_shippingZoneCreate {
  __typename: "ShippingZoneCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CreateShippingZone_shippingZoneCreate_errors[] | null;
  shippingZone: CreateShippingZone_shippingZoneCreate_shippingZone | null;
}

export interface CreateShippingZone {
  /**
   * Creates a new shipping zone.
   */
  shippingZoneCreate: CreateShippingZone_shippingZoneCreate | null;
}

export interface CreateShippingZoneVariables {
  input: ShippingZoneInput;
}
