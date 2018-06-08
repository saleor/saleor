import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import DeleteIcon from "@material-ui/icons/Delete";
import EditIcon from "@material-ui/icons/Edit";
import * as React from "react";

import DateFormatter from "../../../components/DateFormatter";
import ExtendedPageHeader from "../../../components/ExtendedPageHeader";
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
    position: "relative" as "relative",
    top: -theme.spacing.unit * 4
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
  }
}));
const CustomerDetails = decorate<CustomerDetailsProps>(
  ({ classes, customer, onDelete, onEdit }) => (
    <Card className={classes.root}>
      <ExtendedPageHeader
        title={
          <div className={classes.header}>
            {customer ? (
              <>
                <Typography variant="title" className={classes.title}>
                  {i18n.t("User details")}
                </Typography>
                <StatusLabel
                  className={classes.status}
                  status={customer.isActive ? "success" : "error"}
                  label={
                    customer.isActive ? i18n.t("Active") : i18n.t("Inactive")
                  }
                />
              </>
            ) : (
              <Skeleton style={{ width: "10rem" }} />
            )}
          </div>
        }
      >
        {!!onEdit && (
          <IconButton onClick={onEdit} disabled={!customer}>
            <EditIcon />
          </IconButton>
        )}
        {!!onDelete && (
          <IconButton onClick={onDelete} disabled={!customer}>
            <DeleteIcon />
          </IconButton>
        )}
      </ExtendedPageHeader>
      <CardContent>
        {customer ? (
          <>
            <div className={classes.date}>
              <Typography
                component="span"
                style={{ display: "inline" }}
                variant="caption"
              >
                {i18n.t("Joined")}
              </Typography>{" "}
              <DateFormatter date={customer.dateJoined} typography="caption" />
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
