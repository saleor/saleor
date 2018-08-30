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
  user?: {
    email: string;
  };
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
  ({ classes, history, user }) => (
    <div className={classes.root}>
      <PageHeader title={i18n.t("Order history")} />
      {history ? (
        <Timeline>
          {user ? (
            <Form initial={{ content: "" }}>
              {({ change, data, submit }) => (
                <TimelineAddNote
                  content={data.content}
                  onChange={change}
                  onSubmit={submit}
                  user={user}
                />
              )}
            </Form>
          ) : (
            undefined
          )}
          {history
            .slice()
            .reverse()
            .map(event => {
              if (event.type === OrderEvents.NOTE_ADDED) {
                return (
                  <TimelineNote
                    user={event.user}
                    date={event.date}
                    content={event.message}
                    key={event.id}
                  />
                );
              }
              return (
                <TimelineNode
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
