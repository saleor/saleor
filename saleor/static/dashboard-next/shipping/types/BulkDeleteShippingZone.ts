/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: BulkDeleteShippingZone
// ====================================================

export interface BulkDeleteShippingZone_shippingZoneBulkDelete_errors {
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

export interface BulkDeleteShippingZone_shippingZoneBulkDelete {
  __typename: "ShippingZoneBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: BulkDeleteShippingZone_shippingZoneBulkDelete_errors[] | null;
}

export interface BulkDeleteShippingZone {
  /**
   * Deletes shipping zones.
   */
  shippingZoneBulkDelete: BulkDeleteShippingZone_shippingZoneBulkDelete | null;
}

export interface BulkDeleteShippingZoneVariables {
  ids: (string | null)[];
}
