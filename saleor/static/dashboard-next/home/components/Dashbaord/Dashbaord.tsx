import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";
import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
interface MoneyType {
  amount: number;
  currency: string;
}

export interface DashboardProps {
  ownerName: string;
}

const decorate = withStyles(theme => ({
  displayBlock: {
    display: "block"
  },
  flexbox: {
    display: "flex"
  },

  root: {
    display: "grid" as "grid",
    gridColumnGap: `${theme.spacing.unit * 3}px`,
    gridTemplateColumns: "2fr 1fr",
    [theme.breakpoints.down("sm")]: {
      gridColumnGap: `${theme.spacing.unit}px`
    },
    [theme.breakpoints.down("xs")]: {
      gridTemplateColumns: "1fr"
    }
  }
}));
const Dashboard = decorate<DashboardProps>(({ ownerName, classes }) => {
  return (
    <Container width="md">
      <PageHeader
        className={classes.displayBlock}
        title={i18n.t("Hello there, {{userName}}", { userName: ownerName })}
      >
        <Typography component="span">
          {i18n.t("Here are some information we gathered about your store")}
        </Typography>
      </PageHeader>

      <div className={classes.root}>
        <div>
          <div className={classes.flexbox}>
            <Card>Sales</Card>
            <Card>Orders</Card>
          </div>

          <CardSpacer />
          <Card>Notification</Card>
          <CardSpacer />
          <Card>ProductListCard</Card>
          <CardSpacer />
        </div>
        <div>
          <Card>HomeActivityCard</Card>
        </div>
      </div>
    </Container>
  );
});
export default Dashboard;
