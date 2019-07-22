/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: BulkDeleteShippingZone
// ====================================================

export interface BulkDeleteShippingZone_shippingZoneBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface BulkDeleteShippingZone_shippingZoneBulkDelete {
  __typename: "ShippingZoneBulkDelete";
  errors: BulkDeleteShippingZone_shippingZoneBulkDelete_errors[] | null;
}

export interface BulkDeleteShippingZone {
  shippingZoneBulkDelete: BulkDeleteShippingZone_shippingZoneBulkDelete | null;
}

export interface BulkDeleteShippingZoneVariables {
  ids: (string | null)[];
}
