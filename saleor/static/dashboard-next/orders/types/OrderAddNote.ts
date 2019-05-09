/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { OrderAddNoteInput, OrderEventsEmailsEnum, OrderEventsEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderAddNote
// ====================================================

export interface OrderAddNote_orderAddNote_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderAddNote_orderAddNote_order_events_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderAddNote_orderAddNote_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmailsEnum | null;
  message: string | null;
  quantity: number | null;
  type: OrderEventsEnum | null;
  user: OrderAddNote_orderAddNote_order_events_user | null;
}

export interface OrderAddNote_orderAddNote_order {
  __typename: "Order";
  id: string;
  events: (OrderAddNote_orderAddNote_order_events | null)[] | null;
}

export interface OrderAddNote_orderAddNote {
  __typename: "OrderAddNote";
  errors: OrderAddNote_orderAddNote_errors[] | null;
  order: OrderAddNote_orderAddNote_order | null;
}

export interface OrderAddNote {
  orderAddNote: OrderAddNote_orderAddNote | null;
}

export interface OrderAddNoteVariables {
  order: string;
  input: OrderAddNoteInput;
}
