import * as React from "react";

import { getMutationProviderData } from "../../misc";
import { PartialMutationProviderOutput } from "../../types";
import {
  TypedOrderAddNoteMutation,
  TypedOrderCancelMutation,
  TypedOrderCaptureMutation,
  TypedOrderCreateFulfillmentMutation,
  TypedOrderDraftCancelMutation,
  TypedOrderDraftFinalizeMutation,
  TypedOrderDraftUpdateMutation,
  TypedOrderFulfillmentCancelMutation,
  TypedOrderFulfillmentUpdateTrackingMutation,
  TypedOrderLineDeleteMutation,
  TypedOrderLinesAddMutation,
  TypedOrderLineUpdateMutation,
  TypedOrderMarkAsPaidMutation,
  TypedOrderRefundMutation,
  TypedOrderShippingMethodUpdateMutation,
  TypedOrderUpdateMutation,
  TypedOrderVoidMutation
} from "../mutations";
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

interface OrderOperationsProps {
  order: string;
  children: (
    props: {
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
    }
  ) => React.ReactNode;
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
  onDraftUpdate,
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
  <TypedOrderVoidMutation onCompleted={onOrderVoid}>
    {(...orderVoid) => (
      <TypedOrderCancelMutation onCompleted={onOrderCancel}>
        {(...orderCancel) => (
          <TypedOrderCaptureMutation onCompleted={onPaymentCapture}>
            {(...paymentCapture) => (
              <TypedOrderRefundMutation onCompleted={onPaymentRefund}>
                {(...paymentRefund) => (
                  <TypedOrderCreateFulfillmentMutation
                    onCompleted={onOrderFulfillmentCreate}
                  >
                    {(...createFulfillment) => (
                      <TypedOrderAddNoteMutation onCompleted={onNoteAdd}>
                        {(...addNote) => (
                          <TypedOrderUpdateMutation onCompleted={onUpdate}>
                            {(...update) => (
                              <TypedOrderDraftUpdateMutation
                                onCompleted={onDraftUpdate}
                              >
                                {(...updateDraft) => (
                                  <TypedOrderShippingMethodUpdateMutation
                                    onCompleted={onShippingMethodUpdate}
                                  >
                                    {(...updateShippingMethod) => (
                                      <TypedOrderLineDeleteMutation
                                        onCompleted={onOrderLineDelete}
                                      >
                                        {(...deleteOrderLine) => (
                                          <TypedOrderLinesAddMutation
                                            onCompleted={onOrderLineAdd}
                                          >
                                            {(...addOrderLine) => (
                                              <TypedOrderLineUpdateMutation
                                                onCompleted={onOrderLineUpdate}
                                              >
                                                {(...updateOrderLine) => (
                                                  <TypedOrderFulfillmentCancelMutation
                                                    onCompleted={
                                                      onOrderFulfillmentCancel
                                                    }
                                                  >
                                                    {(...cancelFulfillment) => (
                                                      <TypedOrderFulfillmentUpdateTrackingMutation
                                                        onCompleted={
                                                          onOrderFulfillmentUpdate
                                                        }
                                                      >
                                                        {(
                                                          ...updateTrackingNumber
                                                        ) => (
                                                          <TypedOrderDraftFinalizeMutation
                                                            onCompleted={
                                                              onDraftFinalize
                                                            }
                                                          >
                                                            {(
                                                              ...finalizeDraft
                                                            ) => (
                                                              <TypedOrderDraftCancelMutation
                                                                onCompleted={
                                                                  onDraftCancel
                                                                }
                                                              >
                                                                {(
                                                                  ...cancelDraft
                                                                ) => (
                                                                  <TypedOrderMarkAsPaidMutation
                                                                    onCompleted={
                                                                      onOrderMarkAsPaid
                                                                    }
                                                                  >
                                                                    {(
                                                                      ...markAsPaid
                                                                    ) =>
                                                                      children({
                                                                        orderAddNote: getMutationProviderData(
                                                                          ...addNote
                                                                        ),
                                                                        orderCancel: getMutationProviderData(
                                                                          ...orderCancel
                                                                        ),
                                                                        orderCreateFulfillment: getMutationProviderData(
                                                                          ...createFulfillment
                                                                        ),
                                                                        orderDraftCancel: getMutationProviderData(
                                                                          ...cancelDraft
                                                                        ),
                                                                        orderDraftFinalize: getMutationProviderData(
                                                                          ...finalizeDraft
                                                                        ),
                                                                        orderDraftUpdate: getMutationProviderData(
                                                                          ...updateDraft
                                                                        ),
                                                                        orderFulfillmentCancel: getMutationProviderData(
                                                                          ...cancelFulfillment
                                                                        ),
                                                                        orderFulfillmentUpdateTracking: getMutationProviderData(
                                                                          ...updateTrackingNumber
                                                                        ),
                                                                        orderLineAdd: getMutationProviderData(
                                                                          ...addOrderLine
                                                                        ),
                                                                        orderLineDelete: getMutationProviderData(
                                                                          ...deleteOrderLine
                                                                        ),
                                                                        orderLineUpdate: getMutationProviderData(
                                                                          ...updateOrderLine
                                                                        ),
                                                                        orderPaymentCapture: getMutationProviderData(
                                                                          ...paymentCapture
                                                                        ),
                                                                        orderPaymentMarkAsPaid: getMutationProviderData(
                                                                          ...markAsPaid
                                                                        ),
                                                                        orderPaymentRefund: getMutationProviderData(
                                                                          ...paymentRefund
                                                                        ),
                                                                        orderShippingMethodUpdate: getMutationProviderData(
                                                                          ...updateShippingMethod
                                                                        ),
                                                                        orderUpdate: getMutationProviderData(
                                                                          ...update
                                                                        ),
                                                                        orderVoid: getMutationProviderData(
                                                                          ...orderVoid
                                                                        )
                                                                      })
                                                                    }
                                                                  </TypedOrderMarkAsPaidMutation>
                                                                )}
                                                              </TypedOrderDraftCancelMutation>
                                                            )}
                                                          </TypedOrderDraftFinalizeMutation>
                                                        )}
                                                      </TypedOrderFulfillmentUpdateTrackingMutation>
                                                    )}
                                                  </TypedOrderFulfillmentCancelMutation>
                                                )}
                                              </TypedOrderLineUpdateMutation>
                                            )}
                                          </TypedOrderLinesAddMutation>
                                        )}
                                      </TypedOrderLineDeleteMutation>
                                    )}
                                  </TypedOrderShippingMethodUpdateMutation>
                                )}
                              </TypedOrderDraftUpdateMutation>
                            )}
                          </TypedOrderUpdateMutation>
                        )}
                      </TypedOrderAddNoteMutation>
                    )}
                  </TypedOrderCreateFulfillmentMutation>
                )}
              </TypedOrderRefundMutation>
            )}
          </TypedOrderCaptureMutation>
        )}
      </TypedOrderCancelMutation>
    )}
  </TypedOrderVoidMutation>
);
export default OrderOperations;
