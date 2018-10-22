import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";
import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import HomeNotificationTable from "../HomeNotificationTable";
import HomeOrdersCard from "../HomeOrdersCard";
import HomeProductListCard from "../HomeProductListCard";
import HomeSalesCard from "../HomeSalesCard";

interface MoneyType {
  amount: number;
  currency: string;
}
export interface DashboardProps {
  daily: {
    orders: {
      amount: number;
    };
    sales: MoneyType;
  };
  notifications: {
    orders: number;
    payments: number;
    problems: number;
    productsOut: number;
  };
  onRowClick: () => undefined;
  ownerName: string;
  topProducts?: Array<{
    id: string;
    name: string;
    orders: number;
    price: MoneyType;
    thumbnailUrl: string;
    variant: string;
  }>;
  toOrders: () => void;
  toPayments: () => void;
  toProblems: () => void;
  toProductsOut: () => void;
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
const Dashboard = decorate<DashboardProps>(
  ({
    ownerName,
    classes,
    daily,
    notifications,
    toOrders,
    toPayments,
    toProblems,
    toProductsOut,
    topProducts,
    onRowClick
  }) => {
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
              <HomeSalesCard disabled={false} title={"Sales"} daily={daily} />
              <HomeOrdersCard disabled={false} title={"Orders"} daily={daily} />
            </div>

            <CardSpacer />
            <HomeNotificationTable
              disabled={false}
              notifications={notifications}
              toOrders={toOrders}
              toPayments={toPayments}
              toProblems={toProblems}
              toProductsOut={toProductsOut}
            />
            <CardSpacer />
            <HomeProductListCard
              onRowClick={onRowClick}
              disabled={false}
              topProducts={topProducts}
            />
            <CardSpacer />
          </div>
          <div>
            <Card>HomeActivityCard</Card>
          </div>
        </div>
      </Container>
    );
  }
);
export default Dashboard;
