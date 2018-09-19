/* tslint:disable */
// This file was automatically generated and should not be edited.

import { OrderEventsEmails, OrderEvents } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OrderEventFragment
// ====================================================

export interface OrderEventFragment_user {
  __typename: "User";
  email: string;
}

export interface OrderEventFragment {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmails | null;
  message: string | null;
  quantity: number | null;
  type: OrderEvents | null;
  user: OrderEventFragment_user | null;
}
