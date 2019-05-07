import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { DateTime } from "../../../components/Date";
import { Hr } from "../../../components/Hr";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CustomerDetails_user } from "../../types/CustomerDetails";

const styles = (theme: Theme) =>
  createStyles({
    label: {
      marginBottom: theme.spacing.unit
    },
    value: {
      fontSize: 24
    }
  });

export interface CustomerStatsProps extends WithStyles<typeof styles> {
  customer: CustomerDetails_user;
}

const CustomerStats = withStyles(styles, { name: "CustomerStats" })(
  ({ classes, customer }: CustomerStatsProps) => (
    <Card>
      <CardTitle title={i18n.t("Customer History")} />
      <CardContent>
        <Typography className={classes.label} variant="caption">
          {i18n.t("Last login")}
        </Typography>
        {maybe(
          () => (
            <Typography variant="title" className={classes.value}>
              {customer.lastLogin === null ? (
                i18n.t("-")
              ) : (
                <DateTime date={customer.lastLogin} />
              )}
            </Typography>
          ),
          <Skeleton />
        )}
      </CardContent>
      <Hr />
      <CardContent>
        <Typography className={classes.label} variant="caption">
          {i18n.t("Last order")}
        </Typography>
        {maybe(
          () => (
            <Typography variant="title" className={classes.value}>
              {customer.lastPlacedOrder.edges.length === 0 ? (
                i18n.t("-")
              ) : (
                <DateTime
                  date={customer.lastPlacedOrder.edges[0].node.created}
                />
              )}
            </Typography>
          ),
          <Skeleton />
        )}
      </CardContent>
    </Card>
  )
);
CustomerStats.displayName = "CustomerStats";
export default CustomerStats;
