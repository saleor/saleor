import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import DateFormatter from "../../../components/DateFormatter";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import i18n from "../../../i18n";

interface CustomerDetailsProps {
  customer?: {
    id: string;
    dateJoined: string;
    email: string;
    isActive: boolean;
    isStaff: boolean;
    note: string;
  };
  onDelete?();
  onEdit?();
}

const decorate = withStyles(theme => ({
  date: {
    marginBottom: theme.spacing.unit * 2
  },
  header: {
    flex: 1,
    paddingBottom: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit * 2
  },
  root: {
    marginBottom: theme.spacing.unit * 2,
    [theme.breakpoints.down("md")]: {
      marginBottom: theme.spacing.unit
    }
  },
  status: {
    marginLeft: theme.spacing.unit * 2,
    position: "relative" as "relative",
    top: -2
  },
  title: {
    display: "inline-block" as "inline-block"
  },
  userJoinDate: {
    display: "inline"
  }
}));
const CustomerDetails = decorate<CustomerDetailsProps>(
  ({ classes, customer, onDelete, onEdit }) => (
    <Card className={classes.root}>
      <CardTitle
        title={i18n.t("User details")}
        toolbar={
          <>
            <Button
              color="secondary"
              variant="flat"
              disabled={!customer}
              onClick={onEdit}
            >
              {i18n.t("Edit customer")}
            </Button>
            <Button
              color="secondary"
              variant="flat"
              disabled={!customer}
              onClick={onDelete}
            >
              {i18n.t("Remove customer")}
            </Button>
          </>
        }
      >
        {customer ? (
          <Typography component="span">
            <StatusLabel
              className={classes.status}
              status={customer.isActive ? "success" : "error"}
              label={customer.isActive ? i18n.t("Active") : i18n.t("Inactive")}
            />
          </Typography>
        ) : (
          <Skeleton style={{ width: "10rem" }} />
        )}
      </CardTitle>
      <CardContent>
        {customer ? (
          <>
            <div className={classes.date}>
              <Typography
                component="span"
                className={classes.userJoinDate}
                variant="caption"
              >
                {i18n.t("Joined")}
              </Typography>{" "}
              <Typography variant="caption">
                <DateFormatter date={customer.dateJoined} />
              </Typography>
            </div>
            {customer.note ? (
              <Typography>{customer.note}</Typography>
            ) : (
              <Typography color="textSecondary">{i18n.t("No note")}</Typography>
            )}
          </>
        ) : (
          <Skeleton />
        )}
      </CardContent>
    </Card>
  )
);
export default CustomerDetails;
