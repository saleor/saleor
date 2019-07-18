/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ShippingZones
// ====================================================

export interface ShippingZones_shippingZones_edges_node_countries {
  __typename: "CountryDisplay";
  /**
   * Country code.
   */
  code: string;
  /**
   * Country name.
   */
  country: string;
}

export interface ShippingZones_shippingZones_edges_node {
  __typename: "ShippingZone";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of countries available for the method.
   */
  countries: (ShippingZones_shippingZones_edges_node_countries | null)[] | null;
  name: string;
}

export interface ShippingZones_shippingZones_edges {
  __typename: "ShippingZoneCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: ShippingZones_shippingZones_edges_node;
}

export interface ShippingZones_shippingZones_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
  /**
   * When paginating backwards, are there more items?
   */
  hasPreviousPage: boolean;
  /**
   * When paginating backwards, the cursor to continue.
   */
  startCursor: string | null;
}

export interface ShippingZones_shippingZones {
  __typename: "ShippingZoneCountableConnection";
  edges: ShippingZones_shippingZones_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: ShippingZones_shippingZones_pageInfo;
}

export interface ShippingZones {
  /**
   * List of the shop's shipping zones.
   */
  shippingZones: ShippingZones_shippingZones | null;
}

export interface ShippingZonesVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
