/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { OrderEventsEmailsEnum, OrderEventsEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: OrderEventFragment
// ====================================================

export interface OrderEventFragment_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderEventFragment {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmailsEnum | null;
  message: string | null;
  quantity: number | null;
  type: OrderEventsEnum | null;
  user: OrderEventFragment_user | null;
}
