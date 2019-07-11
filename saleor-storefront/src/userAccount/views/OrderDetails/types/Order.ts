/* tslint:disable */
// This file was automatically generated and should not be edited.

import {
  PaymentChargeStatusEnum,
  OrderStatus
} from "./../../../../../types/globalTypes";

// ====================================================
// GraphQL query operation: Order
// ====================================================

export interface Order_orderByToken_shippingAddress_country {
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

export interface Order_orderByToken_shippingAddress {
  __typename: "Address";
  firstName: string;
  lastName: string;
  companyName: string;
  streetAddress1: string;
  streetAddress2: string;
  city: string;
  postalCode: string;
  /**
   * Default shop's country
   */
  country: Order_orderByToken_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface Order_orderByToken_lines_variant_price {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface Order_orderByToken_lines_variant_product_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
  /**
   * Alt text for an image.
   */
  alt: string | null;
}

export interface Order_orderByToken_lines_variant_product_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface Order_orderByToken_lines_variant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: Order_orderByToken_lines_variant_product_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: Order_orderByToken_lines_variant_product_thumbnail2x | null;
}

export interface Order_orderByToken_lines_variant {
  __typename: "ProductVariant";
  /**
   * Quantity of a product available for sale.
   */
  stockQuantity: number;
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Price of the product variant.
   */
  price: Order_orderByToken_lines_variant_price | null;
  product: Order_orderByToken_lines_variant_product;
}

export interface Order_orderByToken_lines {
  __typename: "OrderLine";
  productName: string;
  quantity: number;
  variant: Order_orderByToken_lines_variant | null;
}

export interface Order_orderByToken_subtotal_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface Order_orderByToken_subtotal {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: Order_orderByToken_subtotal_gross;
}

export interface Order_orderByToken_total_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface Order_orderByToken_total {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: Order_orderByToken_total_gross;
}

export interface Order_orderByToken_shippingPrice_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface Order_orderByToken_shippingPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: Order_orderByToken_shippingPrice_gross;
}

export interface Order_orderByToken {
  __typename: "Order";
  /**
   * Internal payment status.
   */
  paymentStatus: PaymentChargeStatusEnum | null;
  status: OrderStatus;
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * User-friendly number of an order.
   */
  number: string | null;
  shippingAddress: Order_orderByToken_shippingAddress | null;
  /**
   * List of order lines for the order
   */
  lines: (Order_orderByToken_lines | null)[];
  /**
   * The sum of line prices not including shipping.
   */
  subtotal: Order_orderByToken_subtotal | null;
  /**
   * Total amount of the order.
   */
  total: Order_orderByToken_total | null;
  /**
   * Total price of shipping.
   */
  shippingPrice: Order_orderByToken_shippingPrice | null;
}

export interface Order {
  /**
   * Lookup an order by token.
   */
  orderByToken: Order_orderByToken | null;
}

export interface OrderVariables {
  token: string;
}
