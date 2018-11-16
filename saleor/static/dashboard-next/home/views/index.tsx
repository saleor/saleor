import * as React from "react";

import { UserContext } from "../../auth";
import Navigator from "../../components/Navigator";
import { maybe } from "../../misc";
import { orderListUrl } from "../../orders/urls";
import { productListUrl, productVariantEditUrl } from "../../products";
import { OrderStatusFilter, StockAvailability } from "../../types/globalTypes";
import HomePage from "../components/HomePage";
import { HomePageQuery } from "../queries";

const HomeSection = () => (
  <Navigator>
    {navigate => (
      <UserContext.Consumer>
        {({ user }) => (
          <HomePageQuery>
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
                  navigate(
                    productVariantEditUrl(
                      encodeURIComponent(productId),
                      encodeURIComponent(variantId)
                    )
                  )
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
                productsOutOfStock={maybe(
                  () => data.productsOutOfStock.totalCount
                )}
                userName={user.email}
              />
            )}
          </HomePageQuery>
        )}
      </UserContext.Consumer>
    )}
  </Navigator>
);

export default HomeSection;
