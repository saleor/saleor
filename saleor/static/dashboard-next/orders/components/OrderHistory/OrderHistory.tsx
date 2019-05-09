import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import Form from "../../../components/Form";
import Hr from "../../../components/Hr";
import Skeleton from "../../../components/Skeleton";
import {
  Timeline,
  TimelineAddNote,
  TimelineEvent,
  TimelineNote
} from "../../../components/Timeline";
import i18n from "../../../i18n";
import { OrderEventsEmailsEnum, OrderEventsEnum } from "../../../types/globalTypes";
import { OrderDetails_order_events } from "../../types/OrderDetails";

export interface FormData {
  message: string;
}

const getEventMessage = (event: OrderDetails_order_events) => {
  switch (event.type) {
    case OrderEventsEnum.CANCELED:
      return i18n.t("Order has been cancelled", {
        context: "order history message"
      });
    case OrderEventsEnum.DRAFT_ADDED_PRODUCTS:
      return i18n.t("Products have been added to draft order", {
        context: "order history message"
      });
    case OrderEventsEnum.DRAFT_CREATED:
      return i18n.t("Draft order has been created", {
        context: "order history message"
      });
    case OrderEventsEnum.DRAFT_REMOVED_PRODUCTS:
      return i18n.t("Products have been removed from draft order", {
        context: "order history message"
      });
    case OrderEventsEnum.EMAIL_SENT:
      switch (event.emailType) {
        case OrderEventsEmailsEnum.DIGITAL_LINKS:
          return i18n.t("Links to the order's digital goods have been sent", {
            context: "order history message"
          });
        case OrderEventsEmailsEnum.FULFILLMENT_CONFIRMATION:
          return i18n.t("Fulfillment confirmation has been sent to customer", {
            context: "order history message"
          });
        case OrderEventsEmailsEnum.ORDER_CONFIRMATION:
          return i18n.t("Order confirmation has been sent to customer", {
            context: "order history message"
          });
        case OrderEventsEmailsEnum.PAYMENT_CONFIRMATION:
          return i18n.t("Payment confirmation has been sent to customer", {
            context: "order history message"
          });
        case OrderEventsEmailsEnum.SHIPPING_CONFIRMATION:
          return i18n.t("Shipping details has been sent to customer", {
            context: "order history message"
          });
        case OrderEventsEmailsEnum.TRACKING_UPDATED:
          return i18n.t("Shipping tracking number has been sent to customer", {
            context: "order history message"
          });
      }
    case OrderEventsEnum.FULFILLMENT_CANCELED:
      return i18n.t("Fulfillment has been cancelled", {
        context: "order history message"
      });
    case OrderEventsEnum.FULFILLMENT_FULFILLED_ITEMS:
      return i18n.t("Fulfilled {{ quantity }} items", {
        context: "order history message",
        quantity: event.quantity
      });
    case OrderEventsEnum.FULFILLMENT_RESTOCKED_ITEMS:
      return i18n.t("Restocked {{ quantity }} items", {
        context: "order history message",
        quantity: event.quantity
      });
    case OrderEventsEnum.NOTE_ADDED:
      return i18n.t("Note has been added to the order", {
        context: "order history message"
      });
    case OrderEventsEnum.ORDER_FULLY_PAID:
      return i18n.t("Order has been fully paid", {
        context: "order history message"
      });
    case OrderEventsEnum.ORDER_MARKED_AS_PAID:
      return i18n.t("Marked order as paid", {
        context: "order history message"
      });
    case OrderEventsEnum.OTHER:
      return event.message;
    case OrderEventsEnum.OVERSOLD_ITEMS:
      return i18n.t("Oversold {{ quantity }} items", {
        context: "order history message",
        quantity: event.quantity
      });
    case OrderEventsEnum.PAYMENT_CAPTURED:
      return i18n.t("Payment has been captured", {
        context: "order history message"
      });
    case OrderEventsEnum.PAYMENT_FAILED:
      return i18n.t("Payment failed", {
        context: "order history message"
      });
    case OrderEventsEnum.PAYMENT_REFUNDED:
      return i18n.t("Payment has been refunded", {
        context: "order history message"
      });
    case OrderEventsEnum.PAYMENT_VOIDED:
      return i18n.t("Payment has been voided", {
        context: "order history message"
      });
    case OrderEventsEnum.PLACED:
      return i18n.t("Order has been placed", {
        context: "order history message"
      });
    case OrderEventsEnum.PLACED_FROM_DRAFT:
      return i18n.t("Order has been created from draft", {
        context: "order history message"
      });
    case OrderEventsEnum.TRACKING_UPDATED:
      return i18n.t("Updated fulfillment group's tracking number", {
        context: "order history message"
      });
    case OrderEventsEnum.UPDATED_ADDRESS:
      return i18n.t("Order address has been updated", {
        context: "order history message"
      });
  }
};

const styles = (theme: Theme) =>
  createStyles({
    header: {
      fontWeight: 500,
      marginBottom: theme.spacing.unit
    },
    root: { marginTop: theme.spacing.unit * 4 },
    user: {
      marginBottom: theme.spacing.unit
    }
  });

interface OrderHistoryProps extends WithStyles<typeof styles> {
  history: OrderDetails_order_events[];
  onNoteAdd: (data: FormData) => void;
}

const OrderHistory = withStyles(styles, { name: "OrderHistory" })(
  ({ classes, history, onNoteAdd }: OrderHistoryProps) => (
    <div className={classes.root}>
      <Typography className={classes.header} color="textSecondary">
        {i18n.t("Order History")}
      </Typography>
      <Hr />
      {history ? (
        <Timeline>
          <Form initial={{ message: "" }} onSubmit={onNoteAdd} resetOnSubmit>
            {({ change, data, submit }) => (
              <TimelineAddNote
                message={data.message}
                onChange={change}
                onSubmit={submit}
              />
            )}
          </Form>
          {history
            .slice()
            .reverse()
            .map(event => {
              if (event.type === OrderEventsEnum.NOTE_ADDED) {
                return (
                  <TimelineNote
                    date={event.date}
                    user={event.user}
                    message={event.message}
                    key={event.id}
                  />
                );
              }
              return (
                <TimelineEvent
                  date={event.date}
                  title={getEventMessage(event)}
                  key={event.id}
                />
              );
            })}
        </Timeline>
      ) : (
        <Skeleton />
      )}
    </div>
  )
);
OrderHistory.displayName = "OrderHistory";
export default OrderHistory;
