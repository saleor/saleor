import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { fragmentOrderDetails } from "./queries";
import { OrderCancel, OrderCancelVariables } from "./types/OrderCancel";
import { OrderCapture, OrderCaptureVariables } from "./types/OrderCapture";
import {
  OrderCreateFulfillment,
  OrderCreateFulfillmentVariables
} from "./types/OrderCreateFulfillment";
import { OrderRefund, OrderRefundVariables } from "./types/OrderRefund";
import { OrderRelease, OrderReleaseVariables } from "./types/OrderRelease";

const orderCancelMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderCancel($id: ID!) {
    orderCancel(id: $id, restock: true) {
      order {
        ...OrderDetailsFragment
      }
    }
  }
`;
export const TypedOrderCancelMutation = TypedMutation<
  OrderCancel,
  OrderCancelVariables
>(orderCancelMutation);

const orderRefundMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderRefund($id: ID!, $amount: Decimal!) {
    orderRefund(id: $id, amount: $amount) {
      errors {
        field
        message
      }
      order {
        ...OrderDetailsFragment
      }
    }
  }
`;
export const TypedOrderRefundMutation = TypedMutation<
  OrderRefund,
  OrderRefundVariables
>(orderRefundMutation);

const orderReleaseMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderRelease($id: ID!) {
    orderRelease(id: $id) {
      order {
        ...OrderDetailsFragment
      }
    }
  }
`;
export const TypedOrderReleaseMutation = TypedMutation<
  OrderRelease,
  OrderReleaseVariables
>(orderReleaseMutation);

const orderCaptureMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderCapture($id: ID!, $amount: Decimal!) {
    orderCapture(id: $id, amount: $amount) {
      errors {
        field
        message
      }
      order {
        ...OrderDetailsFragment
      }
    }
  }
`;
export const TypedOrderCaptureMutation = TypedMutation<
  OrderCapture,
  OrderCaptureVariables
>(orderCaptureMutation);

const orderCreateFulfillmentMutation = gql`
  mutation OrderCreateFulfillment($input: FulfillmentCreateInput!) {
    fulfillmentCreate(input: $input) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedOrderCreateFulfillmentMutation = TypedMutation<
  OrderCreateFulfillment,
  OrderCreateFulfillmentVariables
>(orderCreateFulfillmentMutation);
