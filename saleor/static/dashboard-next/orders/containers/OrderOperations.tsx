import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../../types";
import { maybe } from "../../misc";
import { OrderAddNote, OrderAddNoteVariables } from "../types/OrderAddNote";
import { OrderCancel, OrderCancelVariables } from "../types/OrderCancel";
import { OrderCapture, OrderCaptureVariables } from "../types/OrderCapture";
import {
  OrderCreateFulfillment,
  OrderCreateFulfillmentVariables
} from "../types/OrderCreateFulfillment";
import {
  OrderDraftCancel,
  OrderDraftCancelVariables
} from "../types/OrderDraftCancel";
import {
  OrderDraftFinalize,
  OrderDraftFinalizeVariables
} from "../types/OrderDraftFinalize";
import {
  OrderDraftUpdate,
  OrderDraftUpdateVariables
} from "../types/OrderDraftUpdate";
import {
  OrderFulfillmentCancel,
  OrderFulfillmentCancelVariables
} from "../types/OrderFulfillmentCancel";
import {
  OrderFulfillmentUpdateTracking,
  OrderFulfillmentUpdateTrackingVariables
} from "../types/OrderFulfillmentUpdateTracking";
import { OrderLineAdd, OrderLineAddVariables } from "../types/OrderLineAdd";
import {
  OrderLineDelete,
  OrderLineDeleteVariables
} from "../types/OrderLineDelete";
import {
  OrderLineUpdate,
  OrderLineUpdateVariables
} from "../types/OrderLineUpdate";
import {
  OrderMarkAsPaid,
  OrderMarkAsPaidVariables
} from "../types/OrderMarkAsPaid";
import { OrderRefund, OrderRefundVariables } from "../types/OrderRefund";
import {
  OrderShippingMethodUpdate,
  OrderShippingMethodUpdateVariables
} from "../types/OrderShippingMethodUpdate";
import { OrderUpdate, OrderUpdateVariables } from "../types/OrderUpdate";
import { OrderVoid, OrderVoidVariables } from "../types/OrderVoid";
import OrderCancelMutationProvider from "./OrderCancel";
import OrderCreateFulfillmentProvider from "./OrderCreateFulfillment";
import OrderDraftCancelMutationProvider from "./OrderDraftCancel";
import OrderDraftFinalizeMutationProvider from "./OrderDraftFinalize";
import OrderDraftUpdateProvider from "./OrderDraftUpdate";
import OrderFulfillmentCancelProvider from "./OrderFulfillmentCancel";
import OrderFulfillmentUpdateTrackingProvider from "./OrderFulfillmentUpdateTracking";
import OrderLineAddProvider from "./OrderLineAdd";
import OrderLineDeleteProvider from "./OrderLineDelete";
import OrderLineUpdateProvider from "./OrderLineUpdate";
import OrderMarkAsPaidProvider from "./OrderMarkAsPaid";
import OrderNoteAddProvider from "./OrderNoteAdd";
import OrderPaymentCaptureProvider from "./OrderPaymentCapture";
import OrderPaymentRefundProvider from "./OrderPaymentRefund";
import OrderShippingMethodUpdateProvider from "./OrderShippingUpdate";
import OrderUpdateProvider from "./OrderUpdate";
import OrderVoidMutationProvider from "./OrderVoid";

interface OrderOperationsProps extends MutationProviderProps {
  order: string;
  children: MutationProviderRenderProps<{
    orderAddNote: PartialMutationProviderOutput<
      OrderAddNote,
      OrderAddNoteVariables
    >;
    orderCancel: PartialMutationProviderOutput<
      OrderCancel,
      OrderCancelVariables
    >;
    orderCreateFulfillment: PartialMutationProviderOutput<
      OrderCreateFulfillment,
      OrderCreateFulfillmentVariables
    >;
    orderFulfillmentCancel: PartialMutationProviderOutput<
      OrderFulfillmentCancel,
      OrderFulfillmentCancelVariables
    >;
    orderFulfillmentUpdateTracking: PartialMutationProviderOutput<
      OrderFulfillmentUpdateTracking,
      OrderFulfillmentUpdateTrackingVariables
    >;
    orderPaymentCapture: PartialMutationProviderOutput<
      OrderCapture,
      OrderCaptureVariables
    >;
    orderPaymentRefund: PartialMutationProviderOutput<
      OrderRefund,
      OrderRefundVariables
    >;
    orderPaymentMarkAsPaid: PartialMutationProviderOutput<
      OrderMarkAsPaid,
      OrderMarkAsPaidVariables
    >;
    orderVoid: PartialMutationProviderOutput<OrderVoid, OrderVoidVariables>;
    orderUpdate: PartialMutationProviderOutput<
      OrderUpdate,
      OrderUpdateVariables
    >;
    orderDraftCancel: PartialMutationProviderOutput<
      OrderDraftCancel,
      OrderDraftCancelVariables
    >;
    orderDraftFinalize: PartialMutationProviderOutput<
      OrderDraftFinalize,
      OrderDraftFinalizeVariables
    >;
    orderDraftUpdate: PartialMutationProviderOutput<
      OrderDraftUpdate,
      OrderDraftUpdateVariables
    >;
    orderShippingMethodUpdate: PartialMutationProviderOutput<
      OrderShippingMethodUpdate,
      OrderShippingMethodUpdateVariables
    >;
    orderLineDelete: PartialMutationProviderOutput<
      OrderLineDelete,
      OrderLineDeleteVariables
    >;
    orderLineAdd: PartialMutationProviderOutput<
      OrderLineAdd,
      OrderLineAddVariables
    >;
    orderLineUpdate: PartialMutationProviderOutput<
      OrderLineUpdate,
      OrderLineUpdateVariables
    >;
  }>;
  onOrderFulfillmentCancel: (data: OrderFulfillmentCancel) => void;
  onOrderFulfillmentCreate: (data: OrderCreateFulfillment) => void;
  onOrderFulfillmentUpdate: (data: OrderFulfillmentUpdateTracking) => void;
  onOrderCancel: (data: OrderCancel) => void;
  onOrderVoid: (data: OrderVoid) => void;
  onOrderMarkAsPaid: (data: OrderMarkAsPaid) => void;
  onNoteAdd: (data: OrderAddNote) => void;
  onPaymentCapture: (data: OrderCapture) => void;
  onPaymentRefund: (data: OrderRefund) => void;
  onUpdate: (data: OrderUpdate) => void;
  onDraftCancel: (data: OrderDraftCancel) => void;
  onDraftFinalize: (data: OrderDraftFinalize) => void;
  onDraftUpdate: (data: OrderDraftUpdate) => void;
  onShippingMethodUpdate: (data: OrderShippingMethodUpdate) => void;
  onOrderLineDelete: (data: OrderLineDelete) => void;
  onOrderLineAdd: (data: OrderLineAdd) => void;
  onOrderLineUpdate: (data: OrderLineUpdate) => void;
}

const OrderOperations: React.StatelessComponent<OrderOperationsProps> = ({
  children,
  order,
  onDraftUpdate,
  onError,
  onOrderFulfillmentCreate,
  onNoteAdd,
  onOrderCancel,
  onOrderLineAdd,
  onOrderLineDelete,
  onOrderLineUpdate,
  onOrderVoid,
  onPaymentCapture,
  onPaymentRefund,
  onShippingMethodUpdate,
  onUpdate,
  onDraftCancel,
  onDraftFinalize,
  onOrderFulfillmentCancel,
  onOrderFulfillmentUpdate,
  onOrderMarkAsPaid
}) => (
  <OrderVoidMutationProvider onError={onError} onSuccess={onOrderVoid}>
    {orderVoid => (
      <OrderCancelMutationProvider onError={onError} onSuccess={onOrderCancel}>
        {orderCancel => (
          <OrderPaymentCaptureProvider
            id={order}
            onError={onError}
            onSuccess={onPaymentCapture}
          >
            {paymentCapture => (
              <OrderPaymentRefundProvider
                id={order}
                onError={onError}
                onSuccess={onPaymentRefund}
              >
                {paymentRefund => (
                  <OrderCreateFulfillmentProvider
                    id={order}
                    onError={onError}
                    onSuccess={onOrderFulfillmentCreate}
                  >
                    {createFulfillment => (
                      <OrderNoteAddProvider
                        onError={onError}
                        onSuccess={onNoteAdd}
                      >
                        {addNote => (
                          <OrderUpdateProvider
                            onError={onError}
                            onSuccess={onUpdate}
                          >
                            {update => (
                              <OrderDraftUpdateProvider
                                onError={onError}
                                onSuccess={onDraftUpdate}
                              >
                                {updateDraft => (
                                  <OrderShippingMethodUpdateProvider
                                    onError={onError}
                                    onSuccess={onShippingMethodUpdate}
                                  >
                                    {updateShippingMethod => (
                                      <OrderLineDeleteProvider
                                        onError={onError}
                                        onSuccess={onOrderLineDelete}
                                      >
                                        {deleteOrderLine => (
                                          <OrderLineAddProvider
                                            onError={onError}
                                            onSuccess={onOrderLineAdd}
                                          >
                                            {addOrderLine => (
                                              <OrderLineUpdateProvider
                                                onError={onError}
                                                onSuccess={onOrderLineUpdate}
                                              >
                                                {updateOrderLine => (
                                                  <OrderFulfillmentCancelProvider
                                                    onError={onError}
                                                    onSuccess={
                                                      onOrderFulfillmentCancel
                                                    }
                                                  >
                                                    {cancelFulfillment => (
                                                      <OrderFulfillmentUpdateTrackingProvider
                                                        onError={onError}
                                                        onSuccess={
                                                          onOrderFulfillmentUpdate
                                                        }
                                                      >
                                                        {updateTrackingNumber => (
                                                          <OrderDraftFinalizeMutationProvider
                                                            onError={onError}
                                                            onSuccess={
                                                              onDraftFinalize
                                                            }
                                                          >
                                                            {finalizeDraft => (
                                                              <OrderDraftCancelMutationProvider
                                                                onError={
                                                                  onError
                                                                }
                                                                onSuccess={
                                                                  onDraftCancel
                                                                }
                                                              >
                                                                {cancelDraft => (
                                                                  <OrderMarkAsPaidProvider
                                                                    onError={
                                                                      onError
                                                                    }
                                                                    onSuccess={
                                                                      onOrderMarkAsPaid
                                                                    }
                                                                  >
                                                                    {markAsPaid =>
                                                                      children({
                                                                        errors: [
                                                                          ...(maybe(
                                                                            () =>
                                                                              createFulfillment
                                                                                .data
                                                                                .orderFulfillmentCreate
                                                                                .errors
                                                                          )
                                                                            ? createFulfillment
                                                                                .data
                                                                                .orderFulfillmentCreate
                                                                                .errors
                                                                            : []),
                                                                          ...(maybe(
                                                                            () =>
                                                                              cancelFulfillment
                                                                                .data
                                                                                .orderFulfillmentCancel
                                                                                .errors
                                                                          )
                                                                            ? cancelFulfillment
                                                                                .data
                                                                                .orderFulfillmentCancel
                                                                                .errors
                                                                            : []),
                                                                          ...(maybe(
                                                                            () =>
                                                                              updateTrackingNumber
                                                                                .data
                                                                                .orderFulfillmentUpdateTracking
                                                                                .errors
                                                                          )
                                                                            ? updateTrackingNumber
                                                                                .data
                                                                                .orderFulfillmentUpdateTracking
                                                                                .errors
                                                                            : []),
                                                                          ...(maybe(
                                                                            () =>
                                                                              paymentCapture
                                                                                .data
                                                                                .orderCapture
                                                                                .errors
                                                                          )
                                                                            ? paymentCapture
                                                                                .data
                                                                                .orderCapture
                                                                                .errors
                                                                            : []),
                                                                          ...(maybe(
                                                                            () =>
                                                                              paymentRefund
                                                                                .data
                                                                                .orderRefund
                                                                                .errors
                                                                          )
                                                                            ? paymentRefund
                                                                                .data
                                                                                .orderRefund
                                                                                .errors
                                                                            : []),
                                                                          ...(maybe(
                                                                            () =>
                                                                              addNote
                                                                                .data
                                                                                .orderAddNote
                                                                                .errors
                                                                          )
                                                                            ? addNote
                                                                                .data
                                                                                .orderAddNote
                                                                                .errors
                                                                            : []),
                                                                          ...(maybe(
                                                                            () =>
                                                                              update
                                                                                .data
                                                                                .orderUpdate
                                                                                .errors
                                                                          )
                                                                            ? update
                                                                                .data
                                                                                .orderUpdate
                                                                                .errors
                                                                            : []),

                                                                          ...(maybe(
                                                                            () =>
                                                                              updateDraft
                                                                                .data
                                                                                .draftOrderUpdate
                                                                                .errors
                                                                          )
                                                                            ? updateDraft
                                                                                .data
                                                                                .draftOrderUpdate
                                                                                .errors
                                                                            : [])
                                                                        ],
                                                                        orderAddNote: {
                                                                          data:
                                                                            addNote.data,
                                                                          loading:
                                                                            addNote.loading,
                                                                          mutate: variables =>
                                                                            addNote.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderCancel: {
                                                                          data:
                                                                            orderCancel.data,
                                                                          loading:
                                                                            orderCancel.loading,
                                                                          mutate: variables =>
                                                                            orderCancel.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderCreateFulfillment: {
                                                                          data:
                                                                            createFulfillment.data,
                                                                          loading:
                                                                            createFulfillment.loading,
                                                                          mutate: variables =>
                                                                            createFulfillment.mutate(
                                                                              {
                                                                                variables: {
                                                                                  ...variables,
                                                                                  input: {
                                                                                    ...variables.input
                                                                                  },
                                                                                  order
                                                                                }
                                                                              }
                                                                            )
                                                                        },
                                                                        orderDraftCancel: {
                                                                          data:
                                                                            cancelDraft.data,
                                                                          loading:
                                                                            cancelDraft.loading,
                                                                          mutate: variables =>
                                                                            cancelDraft.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderDraftFinalize: {
                                                                          data:
                                                                            finalizeDraft.data,
                                                                          loading:
                                                                            finalizeDraft.loading,
                                                                          mutate: variables =>
                                                                            finalizeDraft.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderDraftUpdate: {
                                                                          data:
                                                                            updateDraft.data,
                                                                          loading:
                                                                            updateDraft.loading,
                                                                          mutate: variables =>
                                                                            updateDraft.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderFulfillmentCancel: {
                                                                          data:
                                                                            cancelFulfillment.data,
                                                                          loading:
                                                                            cancelFulfillment.loading,
                                                                          mutate: variables =>
                                                                            cancelFulfillment.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderFulfillmentUpdateTracking: {
                                                                          data:
                                                                            updateTrackingNumber.data,
                                                                          loading:
                                                                            updateTrackingNumber.loading,
                                                                          mutate: variables =>
                                                                            updateTrackingNumber.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderLineAdd: {
                                                                          data:
                                                                            addOrderLine.data,
                                                                          loading:
                                                                            addOrderLine.loading,
                                                                          mutate: variables =>
                                                                            addOrderLine.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderLineDelete: {
                                                                          data:
                                                                            deleteOrderLine.data,
                                                                          loading:
                                                                            deleteOrderLine.loading,
                                                                          mutate: variables =>
                                                                            deleteOrderLine.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderLineUpdate: {
                                                                          data:
                                                                            updateOrderLine.data,
                                                                          loading:
                                                                            updateOrderLine.loading,
                                                                          mutate: variables =>
                                                                            updateOrderLine.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderPaymentCapture: {
                                                                          data:
                                                                            paymentCapture.data,
                                                                          loading:
                                                                            paymentCapture.loading,
                                                                          mutate: variables =>
                                                                            paymentCapture.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderPaymentMarkAsPaid: {
                                                                          data:
                                                                            markAsPaid.data,
                                                                          loading:
                                                                            markAsPaid.loading,
                                                                          mutate: variables =>
                                                                            markAsPaid.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderPaymentRefund: {
                                                                          data:
                                                                            paymentRefund.data,
                                                                          loading:
                                                                            paymentRefund.loading,
                                                                          mutate: variables =>
                                                                            paymentRefund.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderShippingMethodUpdate: {
                                                                          data:
                                                                            updateShippingMethod.data,
                                                                          loading:
                                                                            updateShippingMethod.loading,
                                                                          mutate: variables =>
                                                                            updateShippingMethod.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderUpdate: {
                                                                          data:
                                                                            update.data,
                                                                          loading:
                                                                            update.loading,
                                                                          mutate: variables =>
                                                                            update.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        },
                                                                        orderVoid: {
                                                                          data:
                                                                            orderVoid.data,
                                                                          loading:
                                                                            orderVoid.loading,
                                                                          mutate: variables =>
                                                                            orderVoid.mutate(
                                                                              {
                                                                                variables
                                                                              }
                                                                            )
                                                                        }
                                                                      })
                                                                    }
                                                                  </OrderMarkAsPaidProvider>
                                                                )}
                                                              </OrderDraftCancelMutationProvider>
                                                            )}
                                                          </OrderDraftFinalizeMutationProvider>
                                                        )}
                                                      </OrderFulfillmentUpdateTrackingProvider>
                                                    )}
                                                  </OrderFulfillmentCancelProvider>
                                                )}
                                              </OrderLineUpdateProvider>
                                            )}
                                          </OrderLineAddProvider>
                                        )}
                                      </OrderLineDeleteProvider>
                                    )}
                                  </OrderShippingMethodUpdateProvider>
                                )}
                              </OrderDraftUpdateProvider>
                            )}
                          </OrderUpdateProvider>
                        )}
                      </OrderNoteAddProvider>
                    )}
                  </OrderCreateFulfillmentProvider>
                )}
              </OrderPaymentRefundProvider>
            )}
          </OrderPaymentCaptureProvider>
        )}
      </OrderCancelMutationProvider>
    )}
  </OrderVoidMutationProvider>
);
export default OrderOperations;
