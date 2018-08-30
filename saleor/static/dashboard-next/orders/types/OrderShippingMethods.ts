/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: OrderShippingMethods
// ====================================================

export interface OrderShippingMethods_shippingZones_edges_node_shippingMethods_edges_node {
  __typename: "ShippingMethod";
  id: string;
  name: string;
}

export interface OrderShippingMethods_shippingZones_edges_node_shippingMethods_edges {
  __typename: "ShippingMethodEdge";
  node: OrderShippingMethods_shippingZones_edges_node_shippingMethods_edges_node | null;
}

export interface OrderShippingMethods_shippingZones_edges_node_shippingMethods {
  __typename: "ShippingMethodConnection";
  edges: (OrderShippingMethods_shippingZones_edges_node_shippingMethods_edges | null)[];
}

export interface OrderShippingMethods_shippingZones_edges_node {
  __typename: "ShippingZone";
  shippingMethods: OrderShippingMethods_shippingZones_edges_node_shippingMethods | null;
}

export interface OrderShippingMethods_shippingZones_edges {
  __typename: "ShippingZoneCountableEdge";
  node: OrderShippingMethods_shippingZones_edges_node;
}

export interface OrderShippingMethods_shippingZones {
  __typename: "ShippingZoneCountableConnection";
  edges: OrderShippingMethods_shippingZones_edges[];
}

export interface OrderShippingMethods {
  shippingZones: OrderShippingMethods_shippingZones | null;
}
