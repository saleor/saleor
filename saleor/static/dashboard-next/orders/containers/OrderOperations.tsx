import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../..";
import {
  OrderCaptureMutation,
  OrderCaptureMutationVariables,
  OrderCreateFulfillmentMutation,
  OrderCreateFulfillmentMutationVariables,
  OrderRefundMutation,
  OrderRefundMutationVariables,
  OrderReleaseMutation,
  OrderReleaseMutationVariables
} from "../../gql-types";
import { maybe } from "../../misc";
import { OrderAddNote, OrderAddNoteVariables } from "../types/OrderAddNote";
import { OrderCancel, OrderCancelVariables } from "../types/OrderCancel";
import { OrderUpdate, OrderUpdateVariables } from "../types/OrderUpdate";
import OrderCancelMutationProvider from "./OrderCancel";
import OrderCreateFulfillmentProvider from "./OrderCreateFulfillment";
import OrderNoteAddProvider from "./OrderNoteAdd";
import OrderPaymentCaptureProvider from "./OrderPaymentCapture";
import OrderPaymentRefundProvider from "./OrderPaymentRefund";
import OrderReleaseMutationProvider from "./OrderRelease";
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
      OrderCreateFulfillmentMutation,
      OrderCreateFulfillmentMutationVariables
    >;
    orderPaymentCapture: PartialMutationProviderOutput<
      OrderCaptureMutation,
      OrderCaptureMutationVariables
    >;
    orderPaymentRefund: PartialMutationProviderOutput<
      OrderRefundMutation,
      OrderRefundMutationVariables
    >;
    orderRelease: PartialMutationProviderOutput<
      OrderReleaseMutation,
      OrderReleaseMutationVariables
    >;
    orderUpdate: PartialMutationProviderOutput<
      OrderUpdate,
      OrderUpdateVariables
    >;
  }>;
  onFulfillmentCreate: (data: OrderCreateFulfillmentMutation) => void;
  onOrderCancel: (data: OrderCancel) => void;
  onOrderRelease: (data: OrderReleaseMutation) => void;
  onNoteAdd: (data: OrderAddNote) => void;
  onPaymentCapture: (data: OrderCaptureMutation) => void;
  onPaymentRefund: (data: OrderRefundMutation) => void;
  onUpdate: (data: OrderUpdate) => void;
}

const OrderOperations: React.StatelessComponent<OrderOperationsProps> = ({
  children,
  order,
  onError,
  onFulfillmentCreate,
  onNoteAdd,
  onPaymentCapture,
  onPaymentRefund,
  onUpdate
}) => (
  <OrderReleaseMutationProvider>
    {orderRelease => (
      <OrderCancelMutationProvider>
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
                    onSuccess={onFulfillmentCreate}
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
                            {update =>
                              children({
                                errors: [
                                  ...maybe(
                                    () =>
                                      createFulfillment.data.fulfillmentCreate
                                        .errors,
                                    []
                                  ),
                                  ...maybe(
                                    () =>
                                      paymentCapture.data.orderCapture.errors,
                                    []
                                  ),
                                  ...maybe(
                                    () => paymentRefund.data.orderRefund.errors,
                                    []
                                  ),
                                  ...maybe(
                                    () => addNote.data.orderAddNote.errors,
                                    []
                                  ),
                                  ...maybe(
                                    () => update.data.orderUpdate.errors,
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
                                    orderCancel.mutate({ variables })
                                },
                                orderCreateFulfillment: {
                                  data: createFulfillment.data,
                                  loading: createFulfillment.loading,
                                  mutate: variables =>
                                    createFulfillment.mutate({
                                      variables: {
                                        ...variables,
                                        input: { ...variables.input, order }
                                      }
                                    })
                                },
                                orderPaymentCapture: {
                                  data: paymentCapture.data,
                                  loading: paymentCapture.loading,
                                  mutate: variables =>
                                    paymentCapture.mutate({ variables })
                                },
                                orderPaymentRefund: {
                                  data: paymentRefund.data,
                                  loading: paymentRefund.loading,
                                  mutate: variables =>
                                    paymentRefund.mutate({ variables })
                                },
                                orderRelease: {
                                  data: orderRelease.data,
                                  loading: orderRelease.loading,
                                  mutate: variables =>
                                    orderRelease.mutate({ variables })
                                },
                                orderUpdate: {
                                  data: update.data,
                                  loading: update.loading,
                                  mutate: variables =>
                                    update.mutate({ variables })
                                }
                              })
                            }
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
