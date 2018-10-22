import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import HomeActivityCard from "../HomeActivityCard";
import HomeHeader from "../HomeHeader";
import HomeOrdersCard from "../HomeOrdersCard";
import HomeProductListCard from "../HomeProductListCard";
import HomeSalesCard from "../HomeSalesCard";

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
  ({ userName, classes, daily, topProducts, onRowClick, activities }) => {
    return (
      <Container width="md">
        <HomeHeader userName={userName} />
        <CardSpacer />
        <div className={classes.root}>
          <div>
            <div className={classes.flexbox}>
              <HomeSalesCard disabled={false} title={"Sales"} daily={daily} />
              <HomeOrdersCard disabled={false} title={"Orders"} daily={daily} />
            </div>

            <CardSpacer />
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
