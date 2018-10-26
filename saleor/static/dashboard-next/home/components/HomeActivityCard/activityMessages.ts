import i18n from "../../../i18n";
import { OrderEvents } from "../../../types/globalTypes";
import { Home_activities_edges_node } from "../../types/home";

export const getActivityMessage = (activity: Home_activities_edges_node) => {
  switch (activity.type) {
    case OrderEvents.ORDER_FULLY_PAID:
      return i18n.t("Order {{ orderId }} had been fully paid", {
        orderId: activity.id
      });
    case OrderEvents.PLACED:
      return i18n.t("Order {{ orderId }} had been placed", {
        orderId: activity.id
      });
    case OrderEvents.PLACED_FROM_DRAFT:
      return i18n.t(
        "Order {{ orderId }} had been placed from draft by {{ user }}",
        {
          orderId: activity.id,
          user: activity.user.email
        }
      );
    default:
      return activity.message;
  }
};
