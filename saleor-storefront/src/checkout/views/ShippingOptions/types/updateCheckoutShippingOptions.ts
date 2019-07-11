/* tslint:disable */
// This file was automatically generated and should not be edited.

import { GatewaysEnum } from "./../../../../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: updateCheckoutShippingOptions
// ====================================================

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_errors {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_user {
  __typename: "User";
  email: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice_gross {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice_gross {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_billingAddress_country {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_billingAddress {
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
  country: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_billingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingAddress_country {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingAddress {
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
  country: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingAddress_country;
  countryArea: string;
  phone: string | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_availableShippingMethods_price {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_availableShippingMethods {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  price: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_availableShippingMethods_price | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingMethod_price {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingMethod {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  price: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingMethod_price | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice_gross {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice_gross {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_price {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_product_thumbnail {
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

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_product_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_product_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_product_thumbnail2x | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant {
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
  price: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_price | null;
  product: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant_product;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines {
  __typename: "CheckoutLine";
  /**
   * The ID of the object.
   */
  id: string;
  quantity: number;
  /**
   * The sum of the checkout line price, taxes and discounts.
   */
  totalPrice: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_totalPrice | null;
  variant: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines_variant;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout {
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
  user: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_user | null;
  /**
   * The sum of the the checkout line prices, with all the taxes,shipping costs, and discounts included.
   */
  totalPrice: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_totalPrice | null;
  /**
   * The price of the checkout before shipping, with taxes included.
   */
  subtotalPrice: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_subtotalPrice | null;
  billingAddress: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_billingAddress | null;
  shippingAddress: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingAddress | null;
  /**
   * Email of a customer
   */
  email: string;
  /**
   * Shipping methods that can be used with this order.
   */
  availableShippingMethods: (updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_availableShippingMethods | null)[];
  shippingMethod: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingMethod | null;
  /**
   * The price of the shipping, with all the taxes included.
   */
  shippingPrice: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_shippingPrice | null;
  /**
   * A list of checkout lines, each containing information about an item in the checkout.
   */
  lines: (updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout_lines | null)[] | null;
}

export interface updateCheckoutShippingOptions_checkoutShippingMethodUpdate {
  __typename: "CheckoutShippingMethodUpdate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_errors[] | null;
  /**
   * An updated checkout
   */
  checkout: updateCheckoutShippingOptions_checkoutShippingMethodUpdate_checkout | null;
}

export interface updateCheckoutShippingOptions {
  checkoutShippingMethodUpdate: updateCheckoutShippingOptions_checkoutShippingMethodUpdate | null;
}

export interface updateCheckoutShippingOptionsVariables {
  checkoutId: string;
  shippingMethodId: string;
}
