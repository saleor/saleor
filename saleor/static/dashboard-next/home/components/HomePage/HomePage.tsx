import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import Grid from "../../../components/Grid";
import Money from "../../../components/Money";
import Skeleton from "../../../components/Skeleton";
import Orders from "../../../icons/Orders";
import Sales from "../../../icons/Sales";
import {
  Home_activities_edges_node,
  Home_productTopToday_edges_node,
  Home_salesToday_gross
} from "../../types/Home";
import HomeActivityCard from "../HomeActivityCard";
import HomeAnalyticsCard from "../HomeAnalyticsCard";
import HomeHeader from "../HomeHeader";
import HomeNotificationTable from "../HomeNotificationTable/HomeNotificationTable";
import HomeProductListCard from "../HomeProductListCard";

const styles = (theme: Theme) =>
  createStyles({
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
    }
  });

export interface HomePageProps extends WithStyles<typeof styles> {
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

const HomePage = withStyles(styles, { name: "HomePage" })(
  ({
    classes,
    userName,
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
  }: HomePageProps) => (
    <Container>
      <HomeHeader userName={userName} />
      <CardSpacer />
      <Grid>
        <div>
          <div className={classes.cardContainer}>
            <HomeAnalyticsCard
              title={"Sales"}
              icon={<Sales fontSize={"inherit"} viewBox="0 0 48 48" />}
            >
              {sales ? (
                <Money money={sales} />
              ) : (
                <Skeleton style={{ width: "5em" }} />
              )}
            </HomeAnalyticsCard>
            <HomeAnalyticsCard
              title={"Orders"}
              icon={<Orders fontSize={"inherit"} viewBox="0 0 48 48" />}
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
      </Grid>
    </Container>
  )
);
HomePage.displayName = "HomePage";
export default HomePage;
