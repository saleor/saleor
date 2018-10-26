import { withStyles } from "@material-ui/core/styles";
import AttachMoney from "@material-ui/icons/AttachMoney";
import LocalShipping from "@material-ui/icons/LocalShipping";
import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import { maybe } from "../../../misc";
import {
  Home_activities_edges_node,
  Home_productTopToday_edges_node,
  Home_salesToday_gross
} from "../../types/home";
import HomeActivityCard from "../HomeActivityCard";
import HomeAnalyticsCard from "../HomeAnalyticsCard";
import HomeHeader from "../HomeHeader";
import HomeNotificationTable from "../HomeNotificationTable/HomeNotificationTable";
import HomeProductListCard from "../HomeProductListCard";

export interface HomePageProps {
  activities: Home_activities_edges_node[];
  orders: number;
  ordersToCapture: number;
  ordersToFulfill: number;
  productsOutOfStock: number;
  sales: Home_salesToday_gross;
  topProducts: Home_productTopToday_edges_node[];
  userName: string;
  onOrdersToCaptureClick: () => void;
  onOrdersToFulfillClick: () => void;
  onProductClick: (productId: string, variantId: string) => void;
  onProductsOutOfStockClick: () => void;
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
const HomePage = decorate<HomePageProps>(
  ({
    userName,
    classes,
    orders,
    sales,
    topProducts,
    onProductClick,
    activities,
    onOrdersToCaptureClick,
    onOrdersToFulfillClick,
    onProductsOutOfStockClick,
    ordersToCapture,
    ordersToFulfill,
    productsOutOfStock
  }) => (
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
              {maybe(
                () => (
                  <Money amount={sales.amount} currency={sales.currency} />
                ),
                <Skeleton style={{ width: "5em" }} />
              )}
            </HomeAnalyticsCard>
            <HomeAnalyticsCard
              title={"Orders"}
              icon={<LocalShipping fontSize={"inherit"} />}
            >
              {orders === undefined ? (
                <Skeleton style={{ width: "5em" }} />
              ) : (
                orders
              )}
            </HomeAnalyticsCard>
          </div>
          <HomeNotificationTable
            onOrdersToCaptureClick={onOrdersToCaptureClick}
            onOrdersToFulfillClick={onOrdersToFulfillClick}
            onProductsOutOfStockClick={onProductsOutOfStockClick}
            ordersToCapture={ordersToCapture}
            ordersToFulfill={ordersToFulfill}
            productsOutOfStock={productsOutOfStock}
          />
          <CardSpacer />
          <HomeProductListCard
            onRowClick={onProductClick}
            topProducts={topProducts}
          />
          <CardSpacer />
        </div>
        <div>
          <HomeActivityCard activities={activities} />
        </div>
      </div>
    </Container>
  )
);
export default HomePage;
