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

interface OrderHistoryProps {
  history?: Array<{
    id: string;
    type: string;
    content: string;
    date: string;
    user: string;
    params?: any;
  }>;
  user?: string;
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
          {history
            .slice()
            .reverse()
            .map(event => {
              if (event.type === "note") {
                return (
                  <TimelineNote
                    user={event.user}
                    date={event.date}
                    content={event.content}
                    key={event.id}
                  />
                );
              }
              if (event.type === "shipped") {
                return (
                  <TimelineNode
                    date={event.date}
                    title={event.content}
                    key={event.id}
                  >
                    <Typography variant="caption" className={classes.user}>
                      {i18n.t("by {{ user }}", { user: event.user })}
                    </Typography>
                    <Typography
                      dangerouslySetInnerHTML={{
                        __html: event.params.shippingAddress
                      }}
                    />
                  </TimelineNode>
                );
              }
              return (
                <TimelineNode
                  date={event.date}
                  title={event.content}
                  key={event.id}
                >
                  <Typography variant="caption">
                    {i18n.t("by {{ user }}", { user: event.user })}
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
