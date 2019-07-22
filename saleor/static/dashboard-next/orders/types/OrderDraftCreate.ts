/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: OrderDraftCreate
// ====================================================

export interface OrderDraftCreate_draftOrderCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderDraftCreate_draftOrderCreate_order {
  __typename: "Order";
  id: string;
}

export interface OrderDraftCreate_draftOrderCreate {
  __typename: "DraftOrderCreate";
  errors: OrderDraftCreate_draftOrderCreate_errors[] | null;
  order: OrderDraftCreate_draftOrderCreate_order | null;
}

export interface OrderDraftCreate {
  draftOrderCreate: OrderDraftCreate_draftOrderCreate | null;
}
