/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ShippingZones
// ====================================================

export interface ShippingZones_shippingZones_edges_node_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface ShippingZones_shippingZones_edges_node {
  __typename: "ShippingZone";
  id: string;
  countries: (ShippingZones_shippingZones_edges_node_countries | null)[] | null;
  name: string;
}

export interface ShippingZones_shippingZones_edges {
  __typename: "ShippingZoneCountableEdge";
  node: ShippingZones_shippingZones_edges_node;
}

export interface ShippingZones_shippingZones_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface ShippingZones_shippingZones {
  __typename: "ShippingZoneCountableConnection";
  edges: ShippingZones_shippingZones_edges[];
  pageInfo: ShippingZones_shippingZones_pageInfo;
}

export interface ShippingZones {
  shippingZones: ShippingZones_shippingZones | null;
}

export interface ShippingZonesVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
