/* tslint:disable */
// This file was automatically generated and should not be edited.

import { DraftOrderInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderDraftUpdate
// ====================================================

export interface OrderDraftUpdate_draftOrderUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_shippingMethod_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
  name: string;
  price: OrderDraftUpdate_draftOrderUpdate_order_shippingMethod_price | null;
}

export interface OrderDraftUpdate_draftOrderUpdate_order {
  __typename: "Order";
  id: string;
  userEmail: string | null;
  shippingMethod: OrderDraftUpdate_draftOrderUpdate_order_shippingMethod | null;
  shippingMethodName: string | null;
}

export interface OrderDraftUpdate_draftOrderUpdate {
  __typename: "DraftOrderUpdate";
  errors: (OrderDraftUpdate_draftOrderUpdate_errors | null)[] | null;
  order: OrderDraftUpdate_draftOrderUpdate_order | null;
}

export interface OrderDraftUpdate {
  draftOrderUpdate: OrderDraftUpdate_draftOrderUpdate | null;
}

export interface OrderDraftUpdateVariables {
  id: string;
  input: DraftOrderInput;
}
