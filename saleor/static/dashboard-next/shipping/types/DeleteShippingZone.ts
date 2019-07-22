/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: DeleteShippingZone
// ====================================================

export interface DeleteShippingZone_shippingZoneDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface DeleteShippingZone_shippingZoneDelete {
  __typename: "ShippingZoneDelete";
  errors: DeleteShippingZone_shippingZoneDelete_errors[] | null;
}

export interface DeleteShippingZone {
  shippingZoneDelete: DeleteShippingZone_shippingZoneDelete | null;
}

export interface DeleteShippingZoneVariables {
  id: string;
}
