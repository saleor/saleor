/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { OrderUpdateShippingInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderShippingMethodUpdate
// ====================================================

export interface OrderShippingMethodUpdate_orderUpdateShipping_errors {
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

export interface OrderShippingMethodUpdate_orderUpdateShipping_order_availableShippingMethods {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface OrderShippingMethodUpdate_orderUpdateShipping_order_shippingMethod_price {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
}

export interface OrderShippingMethodUpdate_orderUpdateShipping_order_shippingMethod {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  price: OrderShippingMethodUpdate_orderUpdateShipping_order_shippingMethod_price | null;
}

export interface OrderShippingMethodUpdate_orderUpdateShipping_order_shippingPrice_gross {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
}

export interface OrderShippingMethodUpdate_orderUpdateShipping_order_shippingPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderShippingMethodUpdate_orderUpdateShipping_order_shippingPrice_gross;
}

export interface OrderShippingMethodUpdate_orderUpdateShipping_order {
  __typename: "Order";
  /**
   * Shipping methods that can be used with this order.
   */
  availableShippingMethods: (OrderShippingMethodUpdate_orderUpdateShipping_order_availableShippingMethods | null)[] | null;
  /**
   * The ID of the object.
   */
  id: string;
  shippingMethod: OrderShippingMethodUpdate_orderUpdateShipping_order_shippingMethod | null;
  shippingMethodName: string | null;
  /**
   * Total price of shipping.
   */
  shippingPrice: OrderShippingMethodUpdate_orderUpdateShipping_order_shippingPrice | null;
}

export interface OrderShippingMethodUpdate_orderUpdateShipping {
  __typename: "OrderUpdateShipping";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: OrderShippingMethodUpdate_orderUpdateShipping_errors[] | null;
  /**
   * Order with updated shipping method.
   */
  order: OrderShippingMethodUpdate_orderUpdateShipping_order | null;
}

export interface OrderShippingMethodUpdate {
  /**
   * Updates a shipping method of the order.
   */
  orderUpdateShipping: OrderShippingMethodUpdate_orderUpdateShipping | null;
}

export interface OrderShippingMethodUpdateVariables {
  id: string;
  input: OrderUpdateShippingInput;
}
