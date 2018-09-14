/* tslint:disable */
// This file was automatically generated and should not be edited.

import { FulfillmentCreateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderCreateFulfillment
// ====================================================

export interface OrderCreateFulfillment_fulfillmentCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderCreateFulfillment_fulfillmentCreate {
  __typename: "FulfillmentCreate";
  errors: (OrderCreateFulfillment_fulfillmentCreate_errors | null)[] | null;
}

export interface OrderCreateFulfillment {
  fulfillmentCreate: OrderCreateFulfillment_fulfillmentCreate | null;
}

export interface OrderCreateFulfillmentVariables {
  input: FulfillmentCreateInput;
}
