import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import DateFormatter from "../../../components/DateFormatter";
import { Hr } from "../../../components/Hr";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CustomerDetails_user } from "../../types/CustomerDetails";

export interface CustomerStatsProps {
  customer: CustomerDetails_user;
}

const decorate = withStyles({
  value: {
    fontSize: 24
  }
});
const CustomerStats = decorate<CustomerStatsProps>(({ classes, customer }) => (
  <Card>
    <CardTitle title={i18n.t("Customer History")} />
    <CardContent>
      <Typography variant="body2">{i18n.t("Last login")}</Typography>
      {maybe(
        () => (
          <Typography variant="title" className={classes.value}>
            <DateFormatter date={customer.lastLogin} />
          </Typography>
        ),
        <Skeleton />
      )}
    </CardContent>
    <Hr />
    <CardContent>
      <Typography variant="body2">{i18n.t("Last order")}</Typography>
      {maybe(
        () => (
          <Typography variant="title" className={classes.value}>
            <DateFormatter
              date={customer.lastPlacedOrder.edges[0].node.created}
            />
          </Typography>
        ),
        <Skeleton />
      )}
    </CardContent>
  </Card>
));
CustomerStats.displayName = "CustomerStats";
export default CustomerStats;
