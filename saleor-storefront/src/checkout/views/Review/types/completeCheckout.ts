/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: completeCheckout
// ====================================================

export interface completeCheckout_checkoutComplete_errors {
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

export interface completeCheckout_checkoutComplete_order {
  __typename: "Order";
  /**
   * The ID of the object.
   */
  id: string;
  token: string;
}

export interface completeCheckout_checkoutComplete {
  __typename: "CheckoutComplete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: completeCheckout_checkoutComplete_errors[] | null;
  /**
   * Placed order
   */
  order: completeCheckout_checkoutComplete_order | null;
}

export interface completeCheckout {
  checkoutComplete: completeCheckout_checkoutComplete | null;
}

export interface completeCheckoutVariables {
  checkoutId: string;
}
