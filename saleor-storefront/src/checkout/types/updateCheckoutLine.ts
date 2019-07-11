/* tslint:disable */
// This file was automatically generated and should not be edited.

import { CheckoutLineInput } from "./../../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: updateCheckoutLine
// ====================================================

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice_gross {
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

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_price {
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

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_product_thumbnail {
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

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_product_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_product {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_product_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_product_thumbnail2x | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant {
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
  price: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_price | null;
  product: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant_product;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_lines {
  __typename: "CheckoutLine";
  /**
   * The ID of the object.
   */
  id: string;
  quantity: number;
  /**
   * The sum of the checkout line price, taxes and discounts.
   */
  totalPrice: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_totalPrice | null;
  variant: updateCheckoutLine_checkoutLinesUpdate_checkout_lines_variant;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice_gross {
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

export interface updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice {
  __typename: "TaxedMoney";
  /**
   * Amount of money including taxes.
   */
  gross: updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice_gross;
  /**
   * Currency code.
   */
  currency: string;
}

export interface updateCheckoutLine_checkoutLinesUpdate_checkout {
  __typename: "Checkout";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * A list of checkout lines, each containing information about an item in the checkout.
   */
  lines: (updateCheckoutLine_checkoutLinesUpdate_checkout_lines | null)[] | null;
  /**
   * The price of the checkout before shipping, with taxes included.
   */
  subtotalPrice: updateCheckoutLine_checkoutLinesUpdate_checkout_subtotalPrice | null;
}

export interface updateCheckoutLine_checkoutLinesUpdate_errors {
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

export interface updateCheckoutLine_checkoutLinesUpdate {
  __typename: "CheckoutLinesUpdate";
  /**
   * An updated Checkout.
   */
  checkout: updateCheckoutLine_checkoutLinesUpdate_checkout | null;
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: updateCheckoutLine_checkoutLinesUpdate_errors[] | null;
}

export interface updateCheckoutLine {
  checkoutLinesUpdate: updateCheckoutLine_checkoutLinesUpdate | null;
}

export interface updateCheckoutLineVariables {
  checkoutId: string;
  lines: (CheckoutLineInput | null)[];
}
