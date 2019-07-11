/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PaymentChargeStatusEnum, OrderStatus } from "./../../../../../types/globalTypes";

// ====================================================
// GraphQL query operation: OrderById
// ====================================================

export interface OrderById_order_shippingAddress_country {
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

export interface OrderById_order_shippingAddress {
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
  country: OrderById_order_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface OrderById_order_lines_variant_price {
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

export interface OrderById_order_lines_variant_product_thumbnail {
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

export interface OrderById_order_lines_variant_product_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface OrderById_order_lines_variant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: OrderById_order_lines_variant_product_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: OrderById_order_lines_variant_product_thumbnail2x | null;
}

export interface OrderById_order_lines_variant {
  __typename: "ProductVariant";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Price of the product variant.
   */
  price: OrderById_order_lines_variant_price | null;
  product: OrderById_order_lines_variant_product;
}

export interface OrderById_order_lines_unitPrice_gross {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
}

export interface OrderById_order_lines_unitPrice {
  __typename: "TaxedMoney";
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Amount of money including taxes.
   */
  gross: OrderById_order_lines_unitPrice_gross;
}

export interface OrderById_order_lines {
  __typename: "OrderLine";
  productName: string;
  quantity: number;
  /**
   * A purchased product variant. Note: this field may be null if the
   * variant has been removed from stock at all.
   */
  variant: OrderById_order_lines_variant | null;
  /**
   * Price of the single item in the order line.
   */
  unitPrice: OrderById_order_lines_unitPrice | null;
}

export interface OrderById_order_subtotal_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface OrderById_order_subtotal {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderById_order_subtotal_gross;
}

export interface OrderById_order_total_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface OrderById_order_total {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderById_order_total_gross;
}

export interface OrderById_order_shippingPrice_gross {
  __typename: "Money";
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface OrderById_order_shippingPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: OrderById_order_shippingPrice_gross;
}

export interface OrderById_order {
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
  shippingAddress: OrderById_order_shippingAddress | null;
  /**
   * List of order lines.
   */
  lines: (OrderById_order_lines | null)[];
  /**
   * The sum of line prices not including shipping.
   */
  subtotal: OrderById_order_subtotal | null;
  /**
   * Total amount of the order.
   */
  total: OrderById_order_total | null;
  /**
   * Total price of shipping.
   */
  shippingPrice: OrderById_order_shippingPrice | null;
}

export interface OrderById {
  /**
   * Lookup an order by ID.
   */
  order: OrderById_order | null;
}

export interface OrderByIdVariables {
  id: string;
}
