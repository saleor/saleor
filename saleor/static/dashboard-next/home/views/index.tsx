import * as React from "react";

import useNavigator from "../../hooks/useNavigator";
import useUser from "../../hooks/useUser";
import { getUserName, maybe } from "../../misc";
import { orderListUrl } from "../../orders/urls";
import { productListUrl, productVariantEditUrl } from "../../products/urls";
import { OrderStatusFilter, StockAvailability } from "../../types/globalTypes";
import HomePage from "../components/HomePage";
import { HomePageQuery } from "../queries";

const HomeSection = () => {
  const navigate = useNavigator();
  const { user } = useUser();

  return (
    <HomePageQuery displayLoader>
      {({ data }) => (
        <HomePage
          activities={maybe(() =>
            data.activities.edges.map(edge => edge.node).reverse()
          )}
          orders={maybe(() => data.ordersToday.totalCount)}
          sales={maybe(() => data.salesToday.gross)}
          topProducts={maybe(() =>
            data.productTopToday.edges.map(edge => edge.node)
          )}
          onProductClick={(productId, variantId) =>
            navigate(productVariantEditUrl(productId, variantId))
          }
          onOrdersToCaptureClick={() =>
            navigate(
              orderListUrl({
                status: OrderStatusFilter.READY_TO_CAPTURE
              })
            )
          }
          onOrdersToFulfillClick={() =>
            navigate(
              orderListUrl({
                status: OrderStatusFilter.READY_TO_FULFILL
              })
            )
          }
          onProductsOutOfStockClick={() =>
            navigate(
              productListUrl({
                status: StockAvailability.OUT_OF_STOCK
              })
            )
          }
          ordersToCapture={maybe(() => data.ordersToCapture.totalCount)}
          ordersToFulfill={maybe(() => data.ordersToFulfill.totalCount)}
          productsOutOfStock={maybe(() => data.productsOutOfStock.totalCount)}
          userName={getUserName(user, true)}
        />
      )}
    </HomePageQuery>
  );
};

export default HomeSection;
