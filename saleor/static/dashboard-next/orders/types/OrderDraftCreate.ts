/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: OrderDraftCreate
// ====================================================

export interface OrderDraftCreate_draftOrderCreate_errors {
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

export interface OrderDraftCreate_draftOrderCreate_order {
  __typename: "Order";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface OrderDraftCreate_draftOrderCreate {
  __typename: "DraftOrderCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: OrderDraftCreate_draftOrderCreate_errors[] | null;
  order: OrderDraftCreate_draftOrderCreate_order | null;
}

export interface OrderDraftCreate {
  /**
   * Creates a new draft order.
   */
  draftOrderCreate: OrderDraftCreate_draftOrderCreate | null;
}
