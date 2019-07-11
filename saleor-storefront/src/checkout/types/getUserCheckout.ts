/* tslint:disable */
// This file was automatically generated and should not be edited.

import { GatewaysEnum } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: getUserCheckout
// ====================================================

export interface getUserCheckout_me_checkout_user {
  __typename: "User";
  email: string;
}

export interface getUserCheckout_me_checkout_totalPrice_gross {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface getUserCheckout_me_checkout_totalPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: getUserCheckout_me_checkout_totalPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface getUserCheckout_me_checkout_subtotalPrice_gross {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface getUserCheckout_me_checkout_subtotalPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: getUserCheckout_me_checkout_subtotalPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface getUserCheckout_me_checkout_billingAddress_country {
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

export interface getUserCheckout_me_checkout_billingAddress {
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
  country: getUserCheckout_me_checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface getUserCheckout_me_checkout_shippingAddress_country {
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

export interface getUserCheckout_me_checkout_shippingAddress {
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
  country: getUserCheckout_me_checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface getUserCheckout_me_checkout_availableShippingMethods_price {
  __typename: "Money";
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface getUserCheckout_me_checkout_availableShippingMethods {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  price: getUserCheckout_me_checkout_availableShippingMethods_price | null;
}

export interface getUserCheckout_me_checkout_shippingMethod_price {
  __typename: "Money";
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface getUserCheckout_me_checkout_shippingMethod {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  price: getUserCheckout_me_checkout_shippingMethod_price | null;
}

export interface getUserCheckout_me_checkout_shippingPrice_gross {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface getUserCheckout_me_checkout_shippingPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: getUserCheckout_me_checkout_shippingPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface getUserCheckout_me_checkout_lines_totalPrice_gross {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface getUserCheckout_me_checkout_lines_totalPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: getUserCheckout_me_checkout_lines_totalPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface getUserCheckout_me_checkout_lines_variant_price {
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

export interface getUserCheckout_me_checkout_lines_variant_product_thumbnail {
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

export interface getUserCheckout_me_checkout_lines_variant_product_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface getUserCheckout_me_checkout_lines_variant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: getUserCheckout_me_checkout_lines_variant_product_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: getUserCheckout_me_checkout_lines_variant_product_thumbnail2x | null;
}

export interface getUserCheckout_me_checkout_lines_variant {
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
  price: getUserCheckout_me_checkout_lines_variant_price | null;
  product: getUserCheckout_me_checkout_lines_variant_product;
}

export interface getUserCheckout_me_checkout_lines {
  __typename: "CheckoutLine";
  /**
   * The ID of the object.
   */
  id: string;
  quantity: number;
  /**
   * The sum of the checkout line price, taxes and discounts.
   */
  totalPrice: getUserCheckout_me_checkout_lines_totalPrice | null;
  variant: getUserCheckout_me_checkout_lines_variant;
}

export interface getUserCheckout_me_checkout {
  __typename: "Checkout";
  /**
   * List of available payment gateways.
   */
  availablePaymentGateways: (GatewaysEnum | null)[];
  token: any;
  /**
   * The ID of the object.
   */
  id: string;
  user: getUserCheckout_me_checkout_user | null;
  /**
   * The sum of the the checkout line prices, with all the taxes,shipping costs, and discounts included.
   */
  totalPrice: getUserCheckout_me_checkout_totalPrice | null;
  /**
   * The price of the checkout before shipping, with taxes included.
   */
  subtotalPrice: getUserCheckout_me_checkout_subtotalPrice | null;
  billingAddress: getUserCheckout_me_checkout_billingAddress | null;
  shippingAddress: getUserCheckout_me_checkout_shippingAddress | null;
  /**
   * Email of a customer
   */
  email: string;
  /**
   * Shipping methods that can be used with this order.
   */
  availableShippingMethods: (getUserCheckout_me_checkout_availableShippingMethods | null)[];
  shippingMethod: getUserCheckout_me_checkout_shippingMethod | null;
  /**
   * The price of the shipping, with all the taxes included.
   */
  shippingPrice: getUserCheckout_me_checkout_shippingPrice | null;
  /**
   * A list of checkout lines, each containing information about an item in the checkout.
   */
  lines: (getUserCheckout_me_checkout_lines | null)[] | null;
}

export interface getUserCheckout_me {
  __typename: "User";
  /**
   * Returns the last open checkout of this user.
   */
  checkout: getUserCheckout_me_checkout | null;
}

export interface getUserCheckout {
  /**
   * Logged in user data.
   */
  me: getUserCheckout_me | null;
}
