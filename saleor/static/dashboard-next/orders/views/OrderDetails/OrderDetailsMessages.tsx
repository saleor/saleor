import * as React from "react";

import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { OrderAddNote } from "../../types/OrderAddNote";
import { OrderCancel } from "../../types/OrderCancel";
import { OrderCapture } from "../../types/OrderCapture";
import { OrderCreateFulfillment } from "../../types/OrderCreateFulfillment";
import { OrderDraftCancel } from "../../types/OrderDraftCancel";
import { OrderDraftFinalize } from "../../types/OrderDraftFinalize";
import { OrderDraftUpdate } from "../../types/OrderDraftUpdate";
import { OrderFulfillmentCancel } from "../../types/OrderFulfillmentCancel";
import { OrderFulfillmentUpdateTracking } from "../../types/OrderFulfillmentUpdateTracking";
import { OrderLineAdd } from "../../types/OrderLineAdd";
import { OrderLineDelete } from "../../types/OrderLineDelete";
import { OrderLineUpdate } from "../../types/OrderLineUpdate";
import { OrderMarkAsPaid } from "../../types/OrderMarkAsPaid";
import { OrderRefund } from "../../types/OrderRefund";
import { OrderShippingMethodUpdate } from "../../types/OrderShippingMethodUpdate";
import { OrderUpdate } from "../../types/OrderUpdate";
import { OrderVoid } from "../../types/OrderVoid";
import { orderListUrl, orderUrl } from "../../urls";

interface OrderDetailsMessages {
  children: (
    props: {
      handleDraftCancel: (data: OrderDraftCancel) => void;
      handleDraftFinalize: (data: OrderDraftFinalize) => void;
      handleDraftUpdate: (data: OrderDraftUpdate) => void;
      handleNoteAdd: (data: OrderAddNote) => void;
      handleOrderCancel: (data: OrderCancel) => void;
      handleOrderFulfillmentCancel: (data: OrderFulfillmentCancel) => void;
      handleOrderFulfillmentCreate: (data: OrderCreateFulfillment) => void;
      handleOrderFulfillmentUpdate: (
        data: OrderFulfillmentUpdateTracking
      ) => void;
      handleOrderLineAdd: (data: OrderLineAdd) => void;
      handleOrderLineDelete: (data: OrderLineDelete) => void;
      handleOrderLineUpdate: (data: OrderLineUpdate) => void;
      handleOrderMarkAsPaid: (data: OrderMarkAsPaid) => void;
      handleOrderVoid: (data: OrderVoid) => void;
      handlePaymentCapture: (data: OrderCapture) => void;
      handlePaymentRefund: (data: OrderRefund) => void;
      handleShippingMethodUpdate: (data: OrderShippingMethodUpdate) => void;
      handleUpdate: (data: OrderUpdate) => void;
    }
  ) => React.ReactNode;
}

export const OrderDetailsMessages: React.StatelessComponent<
  OrderDetailsMessages
> = ({ children }) => (
  <Navigator>
    {navigate => (
      <Messages>
        {pushMessage => {
          const handlePaymentCapture = (data: OrderCapture) => {
            if (!maybe(() => data.orderCapture.errors.length)) {
              pushMessage({
                text: i18n.t("Payment successfully captured", {
                  context: "notification"
                })
              });
            } else {
              pushMessage({
                text: i18n.t("Payment not captured: {{ errorMessage }}", {
                  context: "notification",
                  errorMessage: data.orderCapture.errors.filter(
                    error => error.field === "payment"
                  )[0].message
                })
              });
            }
          };
          const handlePaymentRefund = (data: OrderRefund) => {
            if (!maybe(() => data.orderRefund.errors.length)) {
              pushMessage({
                text: i18n.t("Payment successfully refunded", {
                  context: "notification"
                })
              });
            } else {
              pushMessage({
                text: i18n.t("Payment not refunded: {{ errorMessage }}", {
                  context: "notification",
                  errorMessage: data.orderRefund.errors.filter(
                    error => error.field === "payment"
                  )[0].message
                })
              });
            }
          };
          const handleOrderFulfillmentCreate = (
            data: OrderCreateFulfillment
          ) => {
            if (!maybe(() => data.orderFulfillmentCreate.errors.length)) {
              pushMessage({
                text: i18n.t("Items successfully fulfilled", {
                  context: "notification"
                })
              });
              navigate(orderUrl(data.orderFulfillmentCreate.order.id), true);
            } else {
              pushMessage({
                text: i18n.t("Could not fulfill items", {
                  context: "notification"
                })
              });
            }
          };
          const handleOrderMarkAsPaid = (data: OrderMarkAsPaid) => {
            if (!maybe(() => data.orderMarkAsPaid.errors.length)) {
              pushMessage({
                text: i18n.t("Order marked as paid", {
                  context: "notification"
                })
              });
              navigate(orderUrl(data.orderMarkAsPaid.order.id), true);
            } else {
              pushMessage({
                text: i18n.t("Could not mark order as paid", {
                  context: "notification"
                })
              });
            }
          };
          const handleOrderCancel = (data: OrderCancel) => {
            pushMessage({
              text: i18n.t("Order successfully cancelled", {
                context: "notification"
              })
            });
            navigate(orderUrl(data.orderCancel.order.id), true);
          };
          const handleDraftCancel = () => {
            pushMessage({
              text: i18n.t("Order successfully cancelled", {
                context: "notification"
              })
            });
            navigate(orderListUrl(), true);
          };
          const handleOrderVoid = () => {
            pushMessage({
              text: i18n.t("Order payment successfully voided", {
                context: "notification"
              })
            });
          };
          const handleNoteAdd = (data: OrderAddNote) => {
            if (!maybe(() => data.orderAddNote.errors.length)) {
              pushMessage({
                text: i18n.t("Note successfully added", {
                  context: "notification"
                })
              });
            } else {
              pushMessage({
                text: i18n.t("Could not add note", {
                  context: "notification"
                })
              });
            }
          };
          const handleUpdate = (data: OrderUpdate) => {
            if (!maybe(() => data.orderUpdate.errors.length)) {
              pushMessage({
                text: i18n.t("Order successfully updated", {
                  context: "notification"
                })
              });
              navigate(orderUrl(data.orderUpdate.order.id), true);
            }
          };
          const handleDraftUpdate = (data: OrderDraftUpdate) => {
            if (!maybe(() => data.draftOrderUpdate.errors.length)) {
              pushMessage({
                text: i18n.t("Order successfully updated", {
                  context: "notification"
                })
              });
              navigate(orderUrl(data.draftOrderUpdate.order.id), true);
            }
          };
          const handleShippingMethodUpdate = (
            data: OrderShippingMethodUpdate
          ) => {
            if (!maybe(() => data.orderUpdateShipping.errors.length)) {
              pushMessage({
                text: i18n.t("Shipping method successfully updated", {
                  context: "notification"
                })
              });
            } else {
              pushMessage({
                text: i18n.t("Could not update shipping method", {
                  context: "notification"
                })
              });
            }
            navigate(orderUrl(data.orderUpdateShipping.order.id), true);
          };
          const handleOrderLineDelete = (data: OrderLineDelete) => {
            if (!maybe(() => data.draftOrderLineDelete.errors.length)) {
              pushMessage({
                text: i18n.t("Order line deleted", {
                  context: "notification"
                })
              });
            } else {
              pushMessage({
                text: i18n.t("Could not delete order line", {
                  context: "notification"
                })
              });
            }
          };
          const handleOrderLineAdd = (data: OrderLineAdd) => {
            if (!maybe(() => data.draftOrderLinesCreate.errors.length)) {
              pushMessage({
                text: i18n.t("Order line added", {
                  context: "notification"
                })
              });
              navigate(orderUrl(data.draftOrderLinesCreate.order.id), true);
            } else {
              pushMessage({
                text: i18n.t("Could not create order line", {
                  context: "notification"
                })
              });
            }
          };
          const handleOrderLineUpdate = (data: OrderLineUpdate) => {
            if (!maybe(() => data.draftOrderLineUpdate.errors.length)) {
              pushMessage({
                text: i18n.t("Order line updated", {
                  context: "notification"
                })
              });
            } else {
              pushMessage({
                text: i18n.t("Could not update order line", {
                  context: "notification"
                })
              });
            }
          };
          const handleOrderFulfillmentCancel = (
            data: OrderFulfillmentCancel
          ) => {
            if (!maybe(() => data.orderFulfillmentCancel.errors.length)) {
              pushMessage({
                text: i18n.t("Fulfillment successfully cancelled", {
                  context: "notification"
                })
              });
              navigate(orderUrl(data.orderFulfillmentCancel.order.id), true);
            } else {
              pushMessage({
                text: i18n.t("Could not cancel fulfillment", {
                  context: "notification"
                })
              });
            }
          };
          const handleOrderFulfillmentUpdate = (
            data: OrderFulfillmentUpdateTracking
          ) => {
            if (
              !maybe(() => data.orderFulfillmentUpdateTracking.errors.length)
            ) {
              pushMessage({
                text: i18n.t("Fulfillment successfully updated", {
                  context: "notification"
                })
              });
              navigate(
                orderUrl(data.orderFulfillmentUpdateTracking.order.id),
                true
              );
            } else {
              pushMessage({
                text: i18n.t("Could not update fulfillment", {
                  context: "notification"
                })
              });
            }
          };
          const handleDraftFinalize = (data: OrderDraftFinalize) => {
            if (!maybe(() => data.draftOrderComplete.errors.length)) {
              pushMessage({
                text: i18n.t("Draft order successfully finalized", {
                  context: "notification"
                })
              });
              navigate(orderUrl(data.draftOrderComplete.order.id), true);
            } else {
              pushMessage({
                text: i18n.t("Could not finalize draft", {
                  context: "notification"
                })
              });
            }
          };

          return children({
            handleDraftCancel,
            handleDraftFinalize,
            handleDraftUpdate,
            handleNoteAdd,
            handleOrderCancel,
            handleOrderFulfillmentCancel,
            handleOrderFulfillmentCreate,
            handleOrderFulfillmentUpdate,
            handleOrderLineAdd,
            handleOrderLineDelete,
            handleOrderLineUpdate,
            handleOrderMarkAsPaid,
            handleOrderVoid,
            handlePaymentCapture,
            handlePaymentRefund,
            handleShippingMethodUpdate,
            handleUpdate
          });
        }}
      </Messages>
    )}
  </Navigator>
);
