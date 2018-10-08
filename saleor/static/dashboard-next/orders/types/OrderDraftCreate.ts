/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: OrderDraftCreate
// ====================================================

export interface OrderDraftCreate_draftOrderCreate_order {
  __typename: "Order";
  id: string;
}

export interface OrderDraftCreate_draftOrderCreate {
  __typename: "DraftOrderCreate";
  order: OrderDraftCreate_draftOrderCreate_order | null;
}

export interface OrderDraftCreate {
  draftOrderCreate: OrderDraftCreate_draftOrderCreate | null;
}
