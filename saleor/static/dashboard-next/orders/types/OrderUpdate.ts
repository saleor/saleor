/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { OrderUpdateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderUpdate
// ====================================================

export interface OrderUpdate_orderUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderUpdate_orderUpdate_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderUpdate_orderUpdate_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderUpdate_orderUpdate_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderUpdate_orderUpdate_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderUpdate_orderUpdate_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderUpdate_orderUpdate_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderUpdate_orderUpdate_order {
  __typename: "Order";
  id: string;
  userEmail: string | null;
  billingAddress: OrderUpdate_orderUpdate_order_billingAddress | null;
  shippingAddress: OrderUpdate_orderUpdate_order_shippingAddress | null;
}

export interface OrderUpdate_orderUpdate {
  __typename: "OrderUpdate";
  errors: OrderUpdate_orderUpdate_errors[] | null;
  order: OrderUpdate_orderUpdate_order | null;
}

export interface OrderUpdate {
  orderUpdate: OrderUpdate_orderUpdate | null;
}

export interface OrderUpdateVariables {
  id: string;
  input: OrderUpdateInput;
}
