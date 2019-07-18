/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: DeleteShippingZone
// ====================================================

export interface DeleteShippingZone_shippingZoneDelete_errors {
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

export interface DeleteShippingZone_shippingZoneDelete {
  __typename: "ShippingZoneDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: DeleteShippingZone_shippingZoneDelete_errors[] | null;
}

export interface DeleteShippingZone {
  /**
   * Deletes a shipping zone.
   */
  shippingZoneDelete: DeleteShippingZone_shippingZoneDelete | null;
}

export interface DeleteShippingZoneVariables {
  id: string;
}
