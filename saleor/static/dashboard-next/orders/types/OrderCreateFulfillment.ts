/* tslint:disable */
// This file was automatically generated and should not be edited.

import { FulfillmentCreateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderCreateFulfillment
// ====================================================

export interface OrderCreateFulfillment_orderFulfillmentCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate {
  __typename: "FulfillmentCreate";
  errors: (OrderCreateFulfillment_orderFulfillmentCreate_errors | null)[] | null;
}

export interface OrderCreateFulfillment {
  orderFulfillmentCreate: OrderCreateFulfillment_orderFulfillmentCreate | null;
}

export interface OrderCreateFulfillmentVariables {
  input: FulfillmentCreateInput;
}
