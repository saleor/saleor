import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import {
  Timeline,
  TimelineAddNote,
  TimelineNode,
  TimelineNote
} from "../../../components/Timeline/Timeline";
import i18n from "../../../i18n";
import { OrderEvents } from "../../../types/globalTypes";

export interface FormData {
  message: string;
}

interface OrderHistoryProps {
  history?: Array<{
    amount?: number;
    date: string;
    email?: string;
    emailType?: string;
    id: string;
    message?: string;
    quantity?: number;
    type: OrderEvents;
    user: {
      email: string;
    };
  }>;
  onNoteAdd: (data: FormData) => void;
}

const decorate = withStyles(
  theme => ({
    root: { marginTop: theme.spacing.unit * 2 },
    user: {
      marginBottom: theme.spacing.unit
    }
  }),
  { name: "OrderHistory" }
);
const OrderHistory = decorate<OrderHistoryProps>(
  ({ classes, history, onNoteAdd }) => (
    <div className={classes.root}>
      <PageHeader title={i18n.t("Order history")} />
      {history ? (
        <Timeline>
          <Form initial={{ message: "" }} onSubmit={onNoteAdd}>
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
              if (event.type === OrderEvents.NOTE_ADDED) {
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
                <TimelineNode
                  amount={event.amount}
                  email={event.email}
                  emailType={event.emailType}
                  quantity={event.quantity}
                  type={event.type}
                  date={event.date}
                  title={event.message}
                  key={event.id}
                >
                  <Typography variant="caption">
                    {i18n.t("by {{ user }}", { user: event.user.email })}
                  </Typography>
                </TimelineNode>
              );
            })}
        </Timeline>
      ) : (
        <Skeleton />
      )}
    </div>
  )
);
export default OrderHistory;
