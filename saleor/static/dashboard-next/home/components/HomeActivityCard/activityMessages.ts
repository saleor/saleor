import i18n from "../../../i18n";
import { OrderEvents, OrderEventsEmails } from "../../../types/globalTypes";
import { Home_activities_edges_node } from "../../types/home";

// FIXME: improve messages
export const getActivityMessage = (activity: Home_activities_edges_node) => {
  switch (activity.type) {
    case OrderEvents.CANCELED:
      return i18n.t("Order {{ id }} had been cancelled by {{ user }}", {
        id: activity.id,
        user: activity.user.email
      });
    case OrderEvents.EMAIL_SENT:
      switch (activity.emailType) {
        case OrderEventsEmails.FULFILLMENT:
          return i18n.t("Fulfillment confirmation has been sent to customer", {
            context: "order history message"
          });
        case OrderEventsEmails.ORDER:
          return i18n.t("Order confirmation has been sent to customer", {
            context: "order history message"
          });
        case OrderEventsEmails.PAYMENT:
          return i18n.t("Payment confirmation has been sent to customer", {
            context: "order history message"
          });
        case OrderEventsEmails.SHIPPING:
          return i18n.t("Shipping details has been sent to customer", {
            context: "order history message"
          });
      }
    case OrderEvents.FULFILLMENT_CANCELED:
      return i18n.t(
        "Fulfillment {{ fulfillmentId }} in order {{ orderId }} had been cancelled by {{ user }}",
        {
          fulfillmentId: activity.composedId,
          orderId: activity.id,
          user: activity.user.email
        }
      );
    case OrderEvents.FULFILLMENT_FULFILLED_ITEMS:
      return i18n.t(
        "Fulfilled {{ amount }} products in order {{ orderId }} by {{ user }}",
        {
          amount: activity.amount,
          orderId: activity.id,
          user: activity.user.email
        }
      );
    case OrderEvents.FULFILLMENT_RESTOCKED_ITEMS:
      return i18n.t(
        "Restocked {{ amounts }} products in order {{ orderId }} by {{ user }}",
        {
          amount: activity.amount,
          orderId: activity.id,
          user: activity.user.email
        }
      );
    case OrderEvents.NOTE_ADDED:
      return i18n.t("Added note to order {{ orderId }} by {{ user }}", {
        orderId: activity.id,
        user: activity.user.email
      });
    case OrderEvents.ORDER_FULLY_PAID:
      return i18n.t("Order {{ orderId }} had been fully paid by {{ user }}", {
        orderId: activity.id
        // user: activity.user.email
      });
    case OrderEvents.ORDER_MARKED_AS_PAID:
      return i18n.t(
        "Order {{ orderId }} had been marked as paid by {{ user }}",
        {
          orderId: activity.id,
          user: activity.user.email
        }
      );
    case OrderEvents.OVERSOLD_ITEMS:
      return i18n.t("Oversold {{ amount }} products in order {{ orderId }}", {
        amount: activity.amount,
        orderId: activity.id
      });
    case OrderEvents.PAYMENT_CAPTURED:
      return i18n.t("Captured payment for order {{ orderId }}", {
        orderId: activity.id
      });
    case OrderEvents.PAYMENT_REFUNDED:
      return i18n.t("Refunded payment for order {{ orderId }} by {{ user }}", {
        orderId: activity.id,
        user: activity.user.email
      });
    case OrderEvents.PAYMENT_RELEASED:
      return i18n.t("Released payment for order {{ orderId }} by {{ user }}", {
        orderId: activity.id,
        user: activity.user.email
      });
    case OrderEvents.PLACED:
      return i18n.t("Order {{ orderId }} had been placed by {{ user }}", {
        orderId: activity.id
        // user: activity.user.email
      });
    case OrderEvents.PLACED_FROM_DRAFT:
      return i18n.t(
        "Order {{ orderId }} had been placed from draft by {{ user }}",
        {
          orderId: activity.id,
          user: activity.user.email
        }
      );
    case OrderEvents.TRACKING_UPDATED:
      return i18n.t(
        "Updated tracking number in fulfillment {{ fulfillmentId }} in order {{ orderId }} by {{ user }}",
        {
          fulfillmentId: activity.composedId,
          orderId: activity.id,
          user: activity.user.email
        }
      );
    case OrderEvents.UPDATED:
      return i18n.t("Order {{ orderId }} had been updated by {{ user }}", {
        orderId: activity.id,
        user: activity.user.email
      });
    default:
      return activity.message;
  }
};
