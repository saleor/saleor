/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ShippingZoneFragment
// ====================================================

export interface ShippingZoneFragment_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface ShippingZoneFragment {
  __typename: "ShippingZone";
  id: string;
  countries: (ShippingZoneFragment_countries | null)[] | null;
  name: string;
}
