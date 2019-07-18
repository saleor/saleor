/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { FulfillmentCancelInput, OrderEventsEmailsEnum, OrderEventsEnum, FulfillmentStatus, PaymentChargeStatusEnum, OrderStatus, OrderAction } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderFulfillmentCancel
// ====================================================

export interface OrderFulfillmentCancel_orderFulfillmentCancel_errors {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_billingAddress_country {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: OrderFulfillmentCancel_orderFulfillmentCancel_order_billingAddress_country;
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_events_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_events {
  __typename: "OrderEvent";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Amount of money.
   */
  amount: number | null;
  /**
   * Date when event happened at in ISO 8601 format.
   */
  date: any | null;
  /**
   * Email of the customer
   */
  email: string | null;
  /**
   * Type of an email sent to the customer
   */
  emailType: OrderEventsEmailsEnum | null;
  /**
   * Content of the event.
   */
  message: string | null;
  /**
   * Number of items.
   */
  quantity: number | null;
  /**
   * Order event type
   */
  type: OrderEventsEnum | null;
  /**
   * User who performed the action.
   */
  user: OrderFulfillmentCancel_orderFulfillmentCancel_order_events_user | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice_gross {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice_net {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice_gross;
  /**
   * Amount of money without taxes.
   */
  net: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice_net;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine {
  __typename: "OrderLine";
  /**
   * The ID of the object.
   */
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  /**
   * Price of the single item in the order line.
   */
  unitPrice: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice | null;
  /**
   * The main thumbnail for the ordered product.
   */
  thumbnail: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_thumbnail | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines {
  __typename: "FulfillmentLine";
  /**
   * The ID of the object.
   */
  id: string;
  quantity: number;
  orderLine: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments {
  __typename: "Fulfillment";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of lines for the fulfillment
   */
  lines: (OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines | null)[] | null;
  fulfillmentOrder: number;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice_gross {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice_net {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice_gross;
  /**
   * Amount of money without taxes.
   */
  net: OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice_net;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines {
  __typename: "OrderLine";
  /**
   * The ID of the object.
   */
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  /**
   * Price of the single item in the order line.
   */
  unitPrice: OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice | null;
  /**
   * The main thumbnail for the ordered product.
   */
  thumbnail: OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_thumbnail | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingAddress_country {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  /**
   * Default shop's country
   */
  country: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingAddress_country;
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingMethod {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingPrice_gross {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingPrice_gross;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_subtotal_gross {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_subtotal {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_subtotal_gross;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_total_gross {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_total_tax {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_total {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_total_gross;
  /**
   * Amount of taxes.
   */
  tax: OrderFulfillmentCancel_orderFulfillmentCancel_order_total_tax;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_totalAuthorized {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_totalCaptured {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_user {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_availableShippingMethods_price {
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

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_availableShippingMethods {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  price: OrderFulfillmentCancel_orderFulfillmentCancel_order_availableShippingMethods_price | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order {
  __typename: "Order";
  /**
   * The ID of the object.
   */
  id: string;
  billingAddress: OrderFulfillmentCancel_orderFulfillmentCancel_order_billingAddress | null;
  /**
   * Informs whether a draft order can be finalized(turned into a regular order).
   */
  canFinalize: boolean;
  created: any;
  customerNote: string;
  /**
   * List of events associated with the order.
   */
  events: (OrderFulfillmentCancel_orderFulfillmentCancel_order_events | null)[] | null;
  /**
   * List of shipments for the order.
   */
  fulfillments: (OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments | null)[];
  /**
   * List of order lines.
   */
  lines: (OrderFulfillmentCancel_orderFulfillmentCancel_order_lines | null)[];
  /**
   * User-friendly number of an order.
   */
  number: string | null;
  /**
   * Internal payment status.
   */
  paymentStatus: PaymentChargeStatusEnum | null;
  shippingAddress: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingAddress | null;
  shippingMethod: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingMethod | null;
  shippingMethodName: string | null;
  /**
   * Total price of shipping.
   */
  shippingPrice: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingPrice | null;
  status: OrderStatus;
  /**
   * The sum of line prices not including shipping.
   */
  subtotal: OrderFulfillmentCancel_orderFulfillmentCancel_order_subtotal | null;
  /**
   * Total amount of the order.
   */
  total: OrderFulfillmentCancel_orderFulfillmentCancel_order_total | null;
  /**
   * List of actions that can be performed in
   *         the current state of an order.
   */
  actions: (OrderAction | null)[];
  /**
   * Amount authorized for the order.
   */
  totalAuthorized: OrderFulfillmentCancel_orderFulfillmentCancel_order_totalAuthorized | null;
  /**
   * Amount captured by payment.
   */
  totalCaptured: OrderFulfillmentCancel_orderFulfillmentCancel_order_totalCaptured | null;
  user: OrderFulfillmentCancel_orderFulfillmentCancel_order_user | null;
  /**
   * Email address of the customer.
   */
  userEmail: string | null;
  /**
   * Shipping methods that can be used with this order.
   */
  availableShippingMethods: (OrderFulfillmentCancel_orderFulfillmentCancel_order_availableShippingMethods | null)[] | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel {
  __typename: "FulfillmentCancel";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: OrderFulfillmentCancel_orderFulfillmentCancel_errors[] | null;
  /**
   * Order which fulfillment was cancelled.
   */
  order: OrderFulfillmentCancel_orderFulfillmentCancel_order | null;
}

export interface OrderFulfillmentCancel {
  /**
   * Cancels existing fulfillment
   *         and optionally restocks items.
   */
  orderFulfillmentCancel: OrderFulfillmentCancel_orderFulfillmentCancel | null;
}

export interface OrderFulfillmentCancelVariables {
  id: string;
  input: FulfillmentCancelInput;
}
