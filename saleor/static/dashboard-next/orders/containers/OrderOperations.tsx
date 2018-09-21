import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../..";
import { maybe } from "../../misc";
import { OrderAddNote, OrderAddNoteVariables } from "../types/OrderAddNote";
import { OrderCancel, OrderCancelVariables } from "../types/OrderCancel";
import { OrderCapture, OrderCaptureVariables } from "../types/OrderCapture";
import {
  OrderCreateFulfillment,
  OrderCreateFulfillmentVariables
} from "../types/OrderCreateFulfillment";
import {
  OrderDraftUpdate,
  OrderDraftUpdateVariables
} from "../types/OrderDraftUpdate";
import {
  OrderLineDelete,
  OrderLineDeleteVariables
} from "../types/OrderLineDelete";
import { OrderRefund, OrderRefundVariables } from "../types/OrderRefund";
import { OrderRelease, OrderReleaseVariables } from "../types/OrderRelease";
import {
  OrderShippingMethodUpdate,
  OrderShippingMethodUpdateVariables
} from "../types/OrderShippingMethodUpdate";
import { OrderUpdate, OrderUpdateVariables } from "../types/OrderUpdate";
import OrderCancelMutationProvider from "./OrderCancel";
import OrderCreateFulfillmentProvider from "./OrderCreateFulfillment";
import OrderDraftUpdateProvider from "./OrderDraftUpdate";
import OrderLineDeleteProvider from "./OrderLineDelete";
import OrderNoteAddProvider from "./OrderNoteAdd";
import OrderPaymentCaptureProvider from "./OrderPaymentCapture";
import OrderPaymentRefundProvider from "./OrderPaymentRefund";
import OrderReleaseMutationProvider from "./OrderRelease";
import OrderShippingMethodUpdateProvider from "./OrderShippingUpdate";
import OrderUpdateProvider from "./OrderUpdate";

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
    orderPaymentCapture: PartialMutationProviderOutput<
      OrderCapture,
      OrderCaptureVariables
    >;
    orderPaymentRefund: PartialMutationProviderOutput<
      OrderRefund,
      OrderRefundVariables
    >;
    orderRelease: PartialMutationProviderOutput<
      OrderRelease,
      OrderReleaseVariables
    >;
    orderUpdate: PartialMutationProviderOutput<
      OrderUpdate,
      OrderUpdateVariables
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
  }>;
  onOrderFulfillmentCreate: (data: OrderCreateFulfillment) => void;
  onOrderCancel: (data: OrderCancel) => void;
  onOrderRelease: (data: OrderRelease) => void;
  onNoteAdd: (data: OrderAddNote) => void;
  onPaymentCapture: (data: OrderCapture) => void;
  onPaymentRefund: (data: OrderRefund) => void;
  onUpdate: (data: OrderUpdate) => void;
  onDraftUpdate: (data: OrderDraftUpdate) => void;
  onShippingMethodUpdate: (data: OrderShippingMethodUpdate) => void;
  onOrderLineDelete: (data: OrderLineDelete) => void;
}

const OrderOperations: React.StatelessComponent<OrderOperationsProps> = ({
  children,
  order,
  onDraftUpdate,
  onError,
  onOrderFulfillmentCreate,
  onNoteAdd,
  onOrderCancel,
  onOrderLineDelete,
  onOrderRelease,
  onPaymentCapture,
  onPaymentRefund,
  onShippingMethodUpdate,
  onUpdate
}) => (
  <OrderReleaseMutationProvider onError={onError} onSuccess={onOrderRelease}>
    {orderRelease => (
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
                                        {deleteOrderLine =>
                                          children({
                                            errors: [
                                              ...maybe(
                                                () =>
                                                  createFulfillment.data
                                                    .orderFulfillmentCreate
                                                    .errors,
                                                []
                                              ),
                                              ...maybe(
                                                () =>
                                                  paymentCapture.data
                                                    .orderCapture.errors,
                                                []
                                              ),
                                              ...maybe(
                                                () =>
                                                  paymentRefund.data.orderRefund
                                                    .errors,
                                                []
                                              ),
                                              ...maybe(
                                                () =>
                                                  addNote.data.orderAddNote
                                                    .errors,
                                                []
                                              ),
                                              ...maybe(
                                                () =>
                                                  update.data.orderUpdate
                                                    .errors,
                                                []
                                              ),

                                              ...maybe(
                                                () =>
                                                  updateDraft.data
                                                    .draftOrderUpdate.errors,
                                                []
                                              )
                                            ],
                                            orderAddNote: {
                                              data: addNote.data,
                                              loading: addNote.loading,
                                              mutate: variables =>
                                                addNote.mutate({ variables })
                                            },
                                            orderCancel: {
                                              data: orderCancel.data,
                                              loading: orderCancel.loading,
                                              mutate: variables =>
                                                orderCancel.mutate({
                                                  variables
                                                })
                                            },
                                            orderCreateFulfillment: {
                                              data: createFulfillment.data,
                                              loading:
                                                createFulfillment.loading,
                                              mutate: variables =>
                                                createFulfillment.mutate({
                                                  variables: {
                                                    ...variables,
                                                    input: {
                                                      ...variables.input
                                                    },
                                                    order
                                                  }
                                                })
                                            },
                                            orderDraftUpdate: {
                                              data: updateDraft.data,
                                              loading: updateDraft.loading,
                                              mutate: variables =>
                                                updateDraft.mutate({
                                                  variables
                                                })
                                            },
                                            orderLineDelete: {
                                              data: deleteOrderLine.data,
                                              loading: deleteOrderLine.loading,
                                              mutate: variables =>
                                                deleteOrderLine.mutate({
                                                  variables
                                                })
                                            },
                                            orderPaymentCapture: {
                                              data: paymentCapture.data,
                                              loading: paymentCapture.loading,
                                              mutate: variables =>
                                                paymentCapture.mutate({
                                                  variables
                                                })
                                            },
                                            orderPaymentRefund: {
                                              data: paymentRefund.data,
                                              loading: paymentRefund.loading,
                                              mutate: variables =>
                                                paymentRefund.mutate({
                                                  variables
                                                })
                                            },
                                            orderRelease: {
                                              data: orderRelease.data,
                                              loading: orderRelease.loading,
                                              mutate: variables =>
                                                orderRelease.mutate({
                                                  variables
                                                })
                                            },
                                            orderShippingMethodUpdate: {
                                              data: updateShippingMethod.data,
                                              loading:
                                                updateShippingMethod.loading,
                                              mutate: variables =>
                                                updateShippingMethod.mutate({
                                                  variables
                                                })
                                            },
                                            orderUpdate: {
                                              data: update.data,
                                              loading: update.loading,
                                              mutate: variables =>
                                                update.mutate({ variables })
                                            }
                                          })
                                        }
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
  </OrderReleaseMutationProvider>
);
export default OrderOperations;
