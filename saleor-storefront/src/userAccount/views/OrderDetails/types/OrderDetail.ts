/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PaymentChargeStatusEnum, OrderStatus } from "./../../../../../types/globalTypes";

// ====================================================
// GraphQL fragment: OrderDetail
// ====================================================

export interface OrderDetail_shippingAddress_country {
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

export interface OrderDetail_shippingAddress {
  __typename: "Address";
  /**
   * The ID of the object.
   */
  id: string;
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
  country: OrderDetail_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface OrderDetail_lines_variant_price {
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

export interface OrderDetail_lines_variant_product_thumbnail {
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

export interface OrderDetail_lines_variant_product_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface OrderDetail_lines_variant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: OrderDetail_lines_variant_product_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: OrderDetail_lines_variant_product_thumbnail2x | null;
}

export interface OrderDetail_lines_variant {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Price of the product variant.
   */
  price: OrderDetail_lines_variant_price | null;
  product: OrderDetail_lines_variant_product;
}

export interface OrderDetail_lines_unitPrice_gross {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
}

export interface OrderDetail_lines_unitPrice {
  __typename: "TaxedMoney";
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Amount of money including taxes.
   */
  gross: OrderDetail_lines_unitPrice_gross;
}

export interface OrderDetail_lines {
  __typename: "OrderLine";
  productName: string;
  quantity: number;
  /**
   * A purchased product variant. Note: this field may be null if the
   * variant has been removed from stock at all.
   */
  variant: OrderDetail_lines_variant | null;
  /**
   * Price of the single item in the order line.
   */
  unitPrice: OrderDetail_lines_unitPrice | null;
}

export interface OrderDetail_subtotal_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface OrderDetail_subtotal {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderDetail_subtotal_gross;
}

export interface OrderDetail_total_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface OrderDetail_total {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderDetail_total_gross;
}

export interface OrderDetail_shippingPrice_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface OrderDetail_shippingPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderDetail_shippingPrice_gross;
}

export interface OrderDetail {
  __typename: "Order";
  /**
   * Email address of the customer.
   */
  userEmail: string | null;
  /**
   * Internal payment status.
   */
  paymentStatus: PaymentChargeStatusEnum | null;
  /**
   * User-friendly payment status.
   */
  paymentStatusDisplay: string | null;
  status: OrderStatus;
  /**
   * User-friendly order status.
   */
  statusDisplay: string | null;
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * User-friendly number of an order.
   */
  number: string | null;
  shippingAddress: OrderDetail_shippingAddress | null;
  /**
   * List of order lines.
   */
  lines: (OrderDetail_lines | null)[];
  /**
   * The sum of line prices not including shipping.
   */
  subtotal: OrderDetail_subtotal | null;
  /**
   * Total amount of the order.
   */
  total: OrderDetail_total | null;
  /**
   * Total price of shipping.
   */
  shippingPrice: OrderDetail_shippingPrice | null;
}
