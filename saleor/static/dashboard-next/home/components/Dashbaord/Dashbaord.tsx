import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import AttachMoney from "@material-ui/icons/AttachMoney";
import LocalShipping from "@material-ui/icons/LocalShipping";
import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import Money from "../../../components/Money";
import HomeActivityCard from "../HomeActivityCard";
import HomeAnalyticsCard from "../HomeAnalyticsCard";
import HomeHeader from "../HomeHeader";
import HomeProductListCard from "../HomeProductListCard";

interface MoneyType {
  amount: number;
  currency: string;
}
export interface DashboardProps {
  activities?: Array<{
    action: string;
    admin: boolean;
    date: string;
    elementName?: string;
    id: string;
    newElement: string;
    user: string;
  }>;
  daily: {
    orders: {
      amount: number;
    };
    sales: MoneyType;
  };
  onRowClick: () => undefined;
  userName: string;
  topProducts: Array<{
    id: string;
    name: string;
    orders: number;
    price: MoneyType;
    thumbnailUrl: string;
    variant: string;
  }>;
}

const decorate = withStyles(theme => ({
  cardContainer: {
    display: "grid",
    gridColumnGap: `${theme.spacing.unit * 3}px`,
    gridTemplateColumns: "1fr 1fr",
    [theme.breakpoints.down("sm")]: {
      gridColumnGap: `${theme.spacing.unit}px`
    },
    [theme.breakpoints.down("xs")]: {
      gridTemplateColumns: "1fr"
    }
  },

  root: {
    display: "grid" as "grid",
    gridColumnGap: `${theme.spacing.unit * 3}px`,
    gridTemplateColumns: "2fr 1fr",
    [theme.breakpoints.down("sm")]: {
      gridColumnGap: `${theme.spacing.unit}px`
    },
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr"
    }
  }
}));
const Dashboard = decorate<DashboardProps>(
  ({ userName, classes, daily, topProducts, onRowClick, activities }) => {
    return (
      <Container width="md">
        <HomeHeader userName={userName} />
        <CardSpacer />
        <div className={classes.root}>
          <div>
            <div className={classes.cardContainer}>
              <HomeAnalyticsCard
                title={"Sales"}
                icon={<AttachMoney fontSize={"inherit"} />}
              >
                {daily && daily.sales ? (
                  <Money
                    amount={daily.sales.amount}
                    currency={daily.sales.currency}
                  />
                ) : (
                  undefined
                )}
              </HomeAnalyticsCard>
              <HomeAnalyticsCard
                title={"Orders"}
                icon={<LocalShipping fontSize={"inherit"} />}
              >
                {daily && daily.orders ? daily.orders.amount : undefined}
              </HomeAnalyticsCard>
            </div>

            <HomeProductListCard
              onRowClick={onRowClick}
              disabled={false}
              topProducts={topProducts}
            />
            <CardSpacer />
          </div>
          <div>
            <HomeActivityCard disabled={false} activities={activities} />
          </div>
        </div>
      </Container>
    );
  }
);
export default Dashboard;
