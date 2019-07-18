/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PaymentChargeStatusEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CustomerDetails
// ====================================================

export interface CustomerDetails_user_defaultShippingAddress_country {
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

export interface CustomerDetails_user_defaultShippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: CustomerDetails_user_defaultShippingAddress_country;
  countryArea: string;
  firstName: string;
  /**
   * The ID of the object.
   */
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface CustomerDetails_user_defaultBillingAddress_country {
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

export interface CustomerDetails_user_defaultBillingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: CustomerDetails_user_defaultBillingAddress_country;
  countryArea: string;
  firstName: string;
  /**
   * The ID of the object.
   */
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface CustomerDetails_user_orders_edges_node_total_gross {
  __typename: "Money";
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Amount of money.
   */
  amount: number;
}

export interface CustomerDetails_user_orders_edges_node_total {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: CustomerDetails_user_orders_edges_node_total_gross;
}

export interface CustomerDetails_user_orders_edges_node {
  __typename: "Order";
  /**
   * The ID of the object.
   */
  id: string;
  created: any;
  /**
   * User-friendly number of an order.
   */
  number: string | null;
  /**
   * Internal payment status.
   */
  paymentStatus: PaymentChargeStatusEnum | null;
  /**
   * Total amount of the order.
   */
  total: CustomerDetails_user_orders_edges_node_total | null;
}

export interface CustomerDetails_user_orders_edges {
  __typename: "OrderCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: CustomerDetails_user_orders_edges_node;
}

export interface CustomerDetails_user_orders {
  __typename: "OrderCountableConnection";
  edges: CustomerDetails_user_orders_edges[];
}

export interface CustomerDetails_user_lastPlacedOrder_edges_node {
  __typename: "Order";
  /**
   * The ID of the object.
   */
  id: string;
  created: any;
}

export interface CustomerDetails_user_lastPlacedOrder_edges {
  __typename: "OrderCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: CustomerDetails_user_lastPlacedOrder_edges_node;
}

export interface CustomerDetails_user_lastPlacedOrder {
  __typename: "OrderCountableConnection";
  edges: CustomerDetails_user_lastPlacedOrder_edges[];
}

export interface CustomerDetails_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  dateJoined: any;
  lastLogin: any | null;
  defaultShippingAddress: CustomerDetails_user_defaultShippingAddress | null;
  defaultBillingAddress: CustomerDetails_user_defaultBillingAddress | null;
  /**
   * A note about the customer
   */
  note: string | null;
  isActive: boolean;
  /**
   * List of user's orders.
   */
  orders: CustomerDetails_user_orders | null;
  /**
   * List of user's orders.
   */
  lastPlacedOrder: CustomerDetails_user_lastPlacedOrder | null;
}

export interface CustomerDetails {
  /**
   * Lookup an user by ID.
   */
  user: CustomerDetails_user | null;
}

export interface CustomerDetailsVariables {
  id: string;
}
