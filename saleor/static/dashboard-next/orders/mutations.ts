import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import {
  fragmentAddress,
  fragmentOrderDetails,
  fragmentOrderEvent
} from "./queries";
import { OrderAddNote, OrderAddNoteVariables } from "./types/OrderAddNote";
import {
  OrderBulkCancel,
  OrderBulkCancelVariables
} from "./types/OrderBulkCancel";
import { OrderCancel, OrderCancelVariables } from "./types/OrderCancel";
import { OrderCapture, OrderCaptureVariables } from "./types/OrderCapture";
import {
  OrderCreateFulfillment,
  OrderCreateFulfillmentVariables
} from "./types/OrderCreateFulfillment";
import {
  OrderDraftBulkCancel,
  OrderDraftBulkCancelVariables
} from "./types/OrderDraftBulkCancel";
import {
  OrderDraftCancel,
  OrderDraftCancelVariables
} from "./types/OrderDraftCancel";
import { OrderDraftCreate } from "./types/OrderDraftCreate";
import {
  OrderDraftFinalize,
  OrderDraftFinalizeVariables
} from "./types/OrderDraftFinalize";
import {
  OrderDraftUpdate,
  OrderDraftUpdateVariables
} from "./types/OrderDraftUpdate";
import {
  OrderFulfillmentCancel,
  OrderFulfillmentCancelVariables
} from "./types/OrderFulfillmentCancel";
import {
  OrderFulfillmentUpdateTracking,
  OrderFulfillmentUpdateTrackingVariables
} from "./types/OrderFulfillmentUpdateTracking";
import {
  OrderLineDelete,
  OrderLineDeleteVariables
} from "./types/OrderLineDelete";
import { OrderLinesAdd, OrderLinesAddVariables } from "./types/OrderLinesAdd";
import {
  OrderLineUpdate,
  OrderLineUpdateVariables
} from "./types/OrderLineUpdate";
import {
  OrderMarkAsPaid,
  OrderMarkAsPaidVariables
} from "./types/OrderMarkAsPaid";
import { OrderRefund, OrderRefundVariables } from "./types/OrderRefund";
import {
  OrderShippingMethodUpdate,
  OrderShippingMethodUpdateVariables
} from "./types/OrderShippingMethodUpdate";
import { OrderUpdate, OrderUpdateVariables } from "./types/OrderUpdate";
import { OrderVoid, OrderVoidVariables } from "./types/OrderVoid";

const orderCancelMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderCancel($id: ID!, $restock: Boolean!) {
    orderCancel(id: $id, restock: $restock) {
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
export const TypedOrderCancelMutation = TypedMutation<
  OrderCancel,
  OrderCancelVariables
>(orderCancelMutation);

const orderBulkCancelMutation = gql`
  mutation OrderBulkCancel($ids: [ID]!, $restock: Boolean!) {
    orderBulkCancel(ids: $ids, restock: $restock) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedOrderBulkCancelMutation = TypedMutation<
  OrderBulkCancel,
  OrderBulkCancelVariables
>(orderBulkCancelMutation);

const orderDraftCancelMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderDraftCancel($id: ID!) {
    draftOrderDelete(id: $id) {
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
export const TypedOrderDraftCancelMutation = TypedMutation<
  OrderDraftCancel,
  OrderDraftCancelVariables
>(orderDraftCancelMutation);

const orderDraftBulkCancelMutation = gql`
  mutation OrderDraftBulkCancel($ids: [ID]!) {
    draftOrderBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedOrderDraftBulkCancelMutation = TypedMutation<
  OrderDraftBulkCancel,
  OrderDraftBulkCancelVariables
>(orderDraftBulkCancelMutation);

const orderDraftFinalizeMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderDraftFinalize($id: ID!) {
    draftOrderComplete(id: $id) {
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
export const TypedOrderDraftFinalizeMutation = TypedMutation<
  OrderDraftFinalize,
  OrderDraftFinalizeVariables
>(orderDraftFinalizeMutation);

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

const orderVoidMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderVoid($id: ID!) {
    orderVoid(id: $id) {
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
export const TypedOrderVoidMutation = TypedMutation<
  OrderVoid,
  OrderVoidVariables
>(orderVoidMutation);

const orderMarkAsPaidMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderMarkAsPaid($id: ID!) {
    orderMarkAsPaid(id: $id) {
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
export const TypedOrderMarkAsPaidMutation = TypedMutation<
  OrderMarkAsPaid,
  OrderMarkAsPaidVariables
>(orderMarkAsPaidMutation);

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
  ${fragmentOrderDetails}
  mutation OrderCreateFulfillment(
    $order: ID!
    $input: FulfillmentCreateInput!
  ) {
    orderFulfillmentCreate(order: $order, input: $input) {
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
export const TypedOrderCreateFulfillmentMutation = TypedMutation<
  OrderCreateFulfillment,
  OrderCreateFulfillmentVariables
>(orderCreateFulfillmentMutation);

const orderFulfillmentUpdateTrackingMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderFulfillmentUpdateTracking(
    $id: ID!
    $input: FulfillmentUpdateTrackingInput!
  ) {
    orderFulfillmentUpdateTracking(id: $id, input: $input) {
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
export const TypedOrderFulfillmentUpdateTrackingMutation = TypedMutation<
  OrderFulfillmentUpdateTracking,
  OrderFulfillmentUpdateTrackingVariables
>(orderFulfillmentUpdateTrackingMutation);

const orderFulfillmentCancelMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderFulfillmentCancel($id: ID!, $input: FulfillmentCancelInput!) {
    orderFulfillmentCancel(id: $id, input: $input) {
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
export const TypedOrderFulfillmentCancelMutation = TypedMutation<
  OrderFulfillmentCancel,
  OrderFulfillmentCancelVariables
>(orderFulfillmentCancelMutation);

const orderAddNoteMutation = gql`
  ${fragmentOrderEvent}
  mutation OrderAddNote($order: ID!, $input: OrderAddNoteInput!) {
    orderAddNote(order: $order, input: $input) {
      errors {
        field
        message
      }
      order {
        id
        events {
          ...OrderEventFragment
        }
      }
    }
  }
`;
export const TypedOrderAddNoteMutation = TypedMutation<
  OrderAddNote,
  OrderAddNoteVariables
>(orderAddNoteMutation);

const orderUpdateMutation = gql`
  ${fragmentAddress}
  mutation OrderUpdate($id: ID!, $input: OrderUpdateInput!) {
    orderUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      order {
        id
        userEmail
        billingAddress {
          ...AddressFragment
        }
        shippingAddress {
          ...AddressFragment
        }
      }
    }
  }
`;
export const TypedOrderUpdateMutation = TypedMutation<
  OrderUpdate,
  OrderUpdateVariables
>(orderUpdateMutation);

const orderDraftUpdateMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderDraftUpdate($id: ID!, $input: DraftOrderInput!) {
    draftOrderUpdate(id: $id, input: $input) {
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
export const TypedOrderDraftUpdateMutation = TypedMutation<
  OrderDraftUpdate,
  OrderDraftUpdateVariables
>(orderDraftUpdateMutation);

const orderShippingMethodUpdateMutation = gql`
  mutation OrderShippingMethodUpdate(
    $id: ID!
    $input: OrderUpdateShippingInput!
  ) {
    orderUpdateShipping(order: $id, input: $input) {
      errors {
        field
        message
      }
      order {
        availableShippingMethods {
          id
          name
        }
        id
        shippingMethod {
          id
          name
          price {
            amount
            currency
          }
        }
        shippingMethodName
        shippingPrice {
          gross {
            amount
            currency
          }
        }
      }
    }
  }
`;
export const TypedOrderShippingMethodUpdateMutation = TypedMutation<
  OrderShippingMethodUpdate,
  OrderShippingMethodUpdateVariables
>(orderShippingMethodUpdateMutation);

const orderDraftCreateMutation = gql`
  mutation OrderDraftCreate {
    draftOrderCreate(input: {}) {
      errors {
        field
        message
      }
      order {
        id
      }
    }
  }
`;
export const TypedOrderDraftCreateMutation = TypedMutation<
  OrderDraftCreate,
  {}
>(orderDraftCreateMutation);

const orderLineDeleteMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderLineDelete($id: ID!) {
    draftOrderLineDelete(id: $id) {
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
export const TypedOrderLineDeleteMutation = TypedMutation<
  OrderLineDelete,
  OrderLineDeleteVariables
>(orderLineDeleteMutation);

const orderLinesAddMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderLinesAdd($id: ID!, $input: [OrderLineCreateInput]!) {
    draftOrderLinesCreate(id: $id, input: $input) {
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
export const TypedOrderLinesAddMutation = TypedMutation<
  OrderLinesAdd,
  OrderLinesAddVariables
>(orderLinesAddMutation);

const orderLineUpdateMutation = gql`
  ${fragmentOrderDetails}
  mutation OrderLineUpdate($id: ID!, $input: OrderLineInput!) {
    draftOrderLineUpdate(id: $id, input: $input) {
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
export const TypedOrderLineUpdateMutation = TypedMutation<
  OrderLineUpdate,
  OrderLineUpdateVariables
>(orderLineUpdateMutation);
